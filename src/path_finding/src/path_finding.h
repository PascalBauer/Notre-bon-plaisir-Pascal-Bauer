/* INCLUDES */

#include <ros/ros.h>
#include <geometry_msgs/PoseArray.h>
#include <tf/transform_listener.h>
#include <geometry_msgs/TransformStamped.h>
#include <std_msgs/Float64.h>
#include <nav_msgs/OccupancyGrid.h>
#include <scenario_msgs/Scenario.h>
#include "RRT.hpp"
#include <geometry_msgs/Point.h>
#include <nav_msgs/Odometry.h>

//lib opencv
#include <opencv2/core/core.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include <opencv2/highgui/highgui.hpp>

/* CONSTANTS */
//#define SMOOTHING_TOLERANCE 5
#define SMOOTHING_STRENGTH 0.5
#define SMOOTHING_TOLERANCE 6
#define SMOOTHING_DATA_WEIGHT 0.5
#define L1 0.01

 /*******Class Path_finding*******/

class PathFinding
{
protected:

    ros::NodeHandle nh_;
    ros::Publisher path_pub;
    tf::TransformListener tf_listener_;

public:

    PathFinding(ros::NodeHandle nh): nh_(nh)
    {
    	path_pub = nh.advertise<geometry_msgs::PoseArray>("path", 1);
    }
    ~PathFinding(){};
    void computeTF();
    vector<Node*> algorithm();
    void destination_point(const scenario_msgs::Scenario::ConstPtr& msg);

};



/* GLOBAL VARIABLES */

nav_msgs::OccupancyGrid map1;
geometry_msgs::PoseArray path1;
std_msgs::Float64 path_feedback1;

double x_robot_origin, y_robot_origin, theta_robot_origin, x_robot_des, y_robot_des, theta_robot_des;


using namespace cv;

/* Headers*/
void affiche_tree(Node *q_i, cv::Mat* map);
void draw_path(std::vector<Node*> path, Mat *map);
std::vector<Node*> rrt_path(Node *end, Node *tree);
std::vector<Node*> path_smoothing(std::vector<Node*> path, Mat *map);
Mat traitement_image(Mat &map);

/* FUNCTIONS */


Mat traitement_image(Mat &map){
  // Gris -> Noir
  for(int i = 0; i < map.rows; i++){
    for(int j = 0; j < map.cols; j++){
      cv::Scalar c = map.at<uchar>(i,j);
      if(c[0] < 240)
        map.at<uchar>(i,j) = 0;
    }
 }
  cv::Mat dst, dst_erode;
  // Erosion/Dilatation
  cv::dilate(map,dst,Mat(), Point(-1,-1) ,5);  
  cv::erode(dst, dst_erode,Mat(), Point(-1,-1), 5);

  return dst_erode;
}



void affiche_tree_rec(Node* q_i,cv::Mat* map){
  int n = q_i->forest.size(), i;
  
  
  for(i=0;i<n;i++){
      
    cv::Point point_q_i(q_i->x,q_i->y);
    cv::Point point_q_f(q_i->forest[i]->x,q_i->forest[i]->y);
    cv::Scalar color_c(0,0,255);
    //std::cout << "(" << q_i->x << "," << q_i->y << ")" << "\t" << "(" << q_i->forest[i]->x << "," << q_i->forest[i]->y << ")" << std::endl; 
    line(*map,point_q_i,point_q_f,color_c);
   
    // recursive call on q_i's forest
    affiche_tree_rec(q_i->forest[i],map);
		
  }
  
  return; 
}

void affiche_tree(Node *tree,cv::Mat* map){	
  return affiche_tree_rec(tree,map);
}

void draw_path(std::vector<Node*> path, Mat *map){

	int n = path.size();

	for(int i=0;i<(n-1);i++){
	
		cv::Point start(path[i]->x,path[i]->y);
		cv::Point end(path[i+1]->x,path[i+1]->y);
		cv::Scalar c(0,0,0);
		cv::line(*map,start,end,c);
	
	}

}

std::vector<Node*> rrt_path(Node *end, Node *tree){
	
	Node *graph_end = closest_to(end, tree), *temp;
	std::vector<Node*> path;
	
	temp = graph_end;
	while(temp){
	
		path.push_back(temp);
		temp = temp->parent;
	
	}
	
	return path;
	
}

std::vector<Node*> path_smoothing(std::vector<Node*> path, Mat *map){

  int n = path.size();
  std::vector<Node*> newpath;
  Node *temp; 
  bool point_ok;
  double change;

  /* Making path deep copy */
  for(int i=0;i<n;i++){
    newpath.push_back(path[i]);
  }

  change = SMOOTHING_TOLERANCE;
  while(change >= SMOOTHING_TOLERANCE){

    change = 0;

    for(int i=1;i<(n-1);i++){
      
      /* updated, better point considered as OK (in map, in free space) */
      temp = new Node(newpath[i]->x,newpath[i]->y);
      
      temp->x += SMOOTHING_STRENGTH*(path[i]->x - temp->x);
      temp->x += SMOOTHING_DATA_WEIGHT*(newpath[i-1]->x + newpath[i+1]->x - 2*temp->x);
      
      temp->y += SMOOTHING_STRENGTH*(path[i]->y - temp->y);
      temp->y += SMOOTHING_DATA_WEIGHT*(newpath[i-1]->y + newpath[i+1]->y - 2*temp->y);
      
      if(_collision_with_object(newpath[i-1],temp,*map) && _collision_with_object(temp,newpath[i+1],*map)){ // if new path (both new trajectories) is OK we can change it
        change += sqrt((temp->x - newpath[i]->x)*(temp->x - newpath[i]->x)+(temp->y - newpath[i]->y)*(temp->y - newpath[i]->  y)); // updating change
        delete newpath[i];
        newpath[i] = temp;
      } 
      else { // else we delete incorrect new node
        delete temp;
      }
      
    }

  }
  return newpath;
}

