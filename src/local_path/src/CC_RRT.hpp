#ifndef CC_RRT_HPP
#define CC_RRT_HPP

#include <cstdlib>
#include <iostream>
#include <ctime>
#include <math.h>

#include <opencv2/core/core.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include <opencv2/highgui/highgui.hpp>


#include "Node.hpp"

//ROBOT_WIDTH 28 cm = 0.28 m = 0.28/map_resolution = 5.6 pixel
#define ROBOT_WIDTH 10

//using namespace std;

static int deltaQ =10;//Don't go up 50
static int nb_in_tree = 0;


Node* closest_to_rec(Node* q_rand, Node* q_i){
  int n = q_i->forest.size();
  double d, d_temp;
  Node  *q_temp,*q_res;

  // we say that q_i is the nearest neighbour as we have not checked its forest yet
  q_res = q_i;

  // distance between q_rand and q_i
  d = sqrt((q_i->x - q_rand->x)*(q_i->x - q_rand->x) + (q_i->y - q_rand->y)*(q_i->y - q_rand->y));

  for(int i=0;i<n;i++){
    // recursive call on q_i's forest
    q_temp = closest_to_rec(q_rand, q_i->forest[i]);

    // distance between q_rand and q_i->forest[i] node
    d_temp = sqrt((q_temp->x - q_rand->x)*(q_temp->x - q_rand->x) + (q_temp->y - q_rand->y)*(q_temp->y - q_rand->y));

    // checking if node q_i->forest[i] node is nearest neighbour and updating if so
    q_res = (d_temp < d) ? q_temp : q_res;

    // updating nearest neighbour's distance found
    d = (d_temp < d) ? d_temp : d;

  }



  return q_res;

}

Node* closest_to(Node* q_rand, Node *tree){
  // Root is first assumed as the nearest neighbour
  return closest_to_rec(q_rand,tree);
}

double norme(Node* n_rand, Node* n_near){
double result=sqrt(pow(n_rand->x - n_near->x,2) + pow(n_rand->y - n_near->y,2));
if(result<1)
{
    result=1;
    return result;
}
else
    return result;

}


bool is_in_map2(int xTemp,int yTemp,int map_size, int x, int y){

    return ((((abs(xTemp + x) >=0) && (xTemp + x < map_size))) && (((abs(yTemp  + y) >=0) && (yTemp  + y < map_size))));
}

bool pixel_test(Node& u, cv::Mat &map, int mode){

 int y_val=0;
 int x_val=0;
 int R=ROBOT_WIDTH;
 int xTemp =  u.x - R;
 int yTemp = u.y - R;

 if(mode == 0){
 // Round of all the square
 for(int i=0;i<2*R;++i)
 {
  	for(int j=0;j<2*R;++j)
  	{
  		{

        if(is_in_map2(xTemp,yTemp,map.cols,i,j)){
             //y_val= yTemp + j   ; x_val = xTemp+i  ;
  		    cv::Scalar h = 0;
            h=(int) map.at<uchar>(yTemp + j,xTemp+i);
   		    //if(h[0] < 254)
  		      //return false;
            if(h[0] >= 254)
                return true;
            else return false;
        }

  		}
  	}
   }
 }

else{
    // Round optimised
if(mode == 1 || mode == 4){
    // Round of the two first lines.
    for (int j = 0; j < 2*R ; ++j)
    {
         if(is_in_map2(xTemp,yTemp,map.cols,0,j)){
         //y_val= yTemp + j   ; x_val = xTemp  ;
         cv::Scalar k = (int) map.at<uchar>(yTemp + j,xTemp );
         if(k[0] < 254)
         return false;
      }
            if(is_in_map2(xTemp,yTemp,map.cols,1,j)){
        //y_val= yTemp + j   ; x_val = xTemp+1  ;
        cv::Scalar l =  (int) map.at<uchar>(yTemp + j ,xTemp+1 );
        if(l[0] < 254)
        return false;
      }
    }
 }
else if(mode == 1 || mode == 2){
    // Round of the two first columns
    for (int i = 0; i < 2*R ; ++i)
    {

        if(is_in_map2(xTemp,yTemp,map.cols,i, 2*R - 1)){
         //y_val= yTemp +  2*R - 1  ; x_val = xTemp+i  ;
         cv::Scalar m = (int)map.at<uchar>(yTemp +  2*R - 1, xTemp+i );
        if(m[0] < 254)
        return false;
      }

         if(is_in_map2(xTemp,yTemp,map.cols,i, 2*R - 2)) {
        //y_val= yTemp +  2*R - 2  ; x_val = xTemp+i  ;
        cv::Scalar n = (int)map.at<uchar>(yTemp +  2*R - 2,xTemp+i );
        if(n[0] < 254)
        return false;
      }
    }
  }

else if(mode == 2 || mode == 3){

       // Round of the two last lines.
    for (int j = 0; j < 2*R ; ++j)
    {

        if(is_in_map2(xTemp,yTemp,map.rows,2*R - 1,j)){
         //y_val= yTemp + j  ; x_val = xTemp+2*R - 1  ;
           cv::Scalar o = (int)map.at<uchar>(yTemp + j,xTemp+2*R - 1  );
        if(o[0] < 254)
        return false;
      }

        if(is_in_map2(xTemp,yTemp,map.rows,2*R - 2 ,j)){
         //y_val= yTemp + j ; x_val = xTemp+2*R - 2  ;
         cv::Scalar p = (int)map.at<uchar>(yTemp + j ,xTemp+2*R - 2  );
        if(p[0] < 254)
        return false;
      }
    }
  }

if(mode == 3 || mode == 4){
     // Round of the two first columns ...
    for (int i = 0; i < 2*R ; ++i)
    {

       if(is_in_map2(xTemp,yTemp,map.rows,i ,0)){
          //y_val= yTemp ; x_val = xTemp + i  ;
            cv::Scalar q =(int) map.at<uchar>(yTemp, xTemp + i );
        if(q[0] < 254)
        return false;
      }

        if(is_in_map2(xTemp,yTemp,map.rows,i ,1)){
         //y_val= yTemp + 1; x_val = xTemp+i  ;
           cv::Scalar r = (int)map.at<uchar>(yTemp + 1,xTemp+i );
        if(r[0] < 254)
         return false;
      }
    }
 }


 }


 return true;
}


bool _collision_with_object(Node* qNew, Node* qNear, cv::Mat &map){
  int delta =0,mode = 0  ;
  Node u;
  u.x = -qNear->x + qNew->x;
  u.y = -qNear->y + qNew->y;
  double normU = norme(qNew,qNear);
  Node n1;
  n1.x = qNear->x + u.x*(delta/normU);
  n1.y = qNear->y + u.y*(delta/normU);
  if (!pixel_test(n1, map, mode))
   return false;
  // Choice of the collision mode depends on the desired direction
  if(qNear->x + u.x*((delta+1)/normU) - n1.x >= 0){
    if(qNear->y + u.y*((delta+1)/normU) - n1.y < 0)
      mode = 1 ;
    else
      mode = 2;
  }
    else{
        if(qNear->y + u.y*((delta+1)/normU) - n1.y < 0)
            mode = 4;
        else
            mode = 3;
  }

    int count=5;

    for(int i = 0; i < 5; i++){
     if((norme(&n1,qNear)<= normU)){
     ++delta;
     n1.x = qNear->x + u.x*(delta/normU);
     n1.y = qNear->y + u.y*(delta/normU);
     if(pixel_test(n1,map,mode) == false)
      return false;
    }
    }

  return true;
}

bool is_in_map(Node* n, cv::Mat m){

    return (((abs(n->x) >= 0) && (n->x < m.rows)) && ((abs(n->y) >=0) && (n->y< m.cols)));
}



bool not_in_free_space(Node* n_rand, cv::Mat map){

  if(!is_in_map(n_rand,map))
    return false;

  cv::Scalar c = map.at<uchar>(n_rand->y,n_rand->x);
 if (c[0] >= 254) return false;
    else return true;
}


void extend(Node* q_rand, Node* tree, cv::Mat map){
    // Find closest to q_rand in tree
    Node *q_near = closest_to(q_rand, tree);

    double norm = norme(q_rand,q_near);

    Node *q_new;
    if(!norm)
    return;
    q_new = new Node(q_near->x + (deltaQ/norm)*(q_rand->x - q_near->x), q_near->y + (deltaQ/norm)*(q_rand->y - q_near->y));
    if(not_in_free_space(q_new,map))
    return;

    // Check the collision on the ligne q_near -> q_new
    if(!_collision_with_object(q_new, q_near, map))
    return;

    // No collision so add it to the tree
    q_new->distFromRoot = norme(q_new,q_near);
    //q_new->distFromRoot = norme(q_new,q_near)/2;
    //Add q_new to the forest of q_near, q_near is the father of q_new
    q_near->forest.push_back(q_new);
    q_new->parent = q_near;
    ++nb_in_tree;


}


void cc_rrt(Node *tree, int k, cv::Mat map,int positionX,int positionY){

  std::srand(std::time(0));
  //while(nb_in_tree < k){
 for(int i = 0; i < k; i++){
    if(nb_in_tree%100==0 && deltaQ >= 5){ // multiple of number of points

      deltaQ = deltaQ -1;
   }

     int x_rand=0,y_rand=0;

        if((positionX < 0)&&(positionY < 0))
        {
        x_rand=((std::rand()% map.rows+1) -map.rows);
        y_rand= ((std::rand()% map.cols+1) -map.cols);
        }
        else if((positionX < 0)&& (positionY >=0)){
        x_rand=((std::rand()% map.rows+1) -map.rows);
        y_rand = (std::rand()% map.cols);
        }
        else if((positionX >= 0)&&(positionY < 0)){
        x_rand=(std::rand()% map.cols);
        y_rand = ((std::rand()% map.cols+1) -map.cols);
        }
        else if((positionX >= 0)&&(positionY >= 0)){
        x_rand=(std::rand()% map.rows);
        y_rand =(std::rand()% map.cols);
        }
    Node* q_rand = new Node(x_rand,y_rand);
    // add distance from root
    extend(q_rand, tree, map);
    //free(q_rand);
  }


}


#endif


