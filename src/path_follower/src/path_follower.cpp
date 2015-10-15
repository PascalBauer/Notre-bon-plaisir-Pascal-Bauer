#include <ros/ros.h>
#include "path_follower.hpp"

void PathFollower::pathCB(const scenario_msgs::Path &msg)
{
	path_uid_ = msg.uid;
    path_ = msg.path;
    index_path_ = 0;
    size_path_ = path_.poses.size();
    if (size_path_ > 0)
	{
		ROS_INFO_STREAM("New path received :   id = " << path_uid_ << "  |  size = " << size_path_ << "  |  goal = "
						<< path_.poses.rbegin()->position.x << " ; " <<path_.poses.rbegin()->position.y);
	}
    else
    {
		ROS_INFO_STREAM("New path received :   id = " << path_uid_ << "  |  size = " << size_path_ << "  |  goal = ");
    }
}


void PathFollower::speedCB(const std_msgs::Float64 &msg)
{
    linear_speed_= msg.data;
}


void PathFollower::computeCmd(double &lin, double &ang)
{
	tf::StampedTransform tf_robot;

    try
    {
        //TODO: replace "map" by path.header.frame_id
        tf_listener_.lookupTransform("/map", robot_frame_, ros::Time(0), tf_robot);
    }
    catch (tf::TransformException ex)
    {
        ROS_ERROR("%s",ex.what());
        ros::Duration(1.0).sleep();
        return;
    }

    double x_robot, y_robot, theta_robot;
    double dx, dy;
    double x_des, y_des;
    double alpha;

    x_robot = tf_robot.getOrigin().x();
    y_robot =  tf_robot.getOrigin().y();
    theta_robot = tf::getYaw(tf_robot.getRotation());

    x_des =  path_.poses[index_path_].position.x;
    y_des =  path_.poses[index_path_].position.y;
    //theta_des = tf::getYaw(path.poses[index_path].orientation);

    dx = x_des - x_robot;
    dy = y_des - y_robot;
    if(du_ == INIT_DU)
    {
        first_du_ = du_;
    }
    du_=sqrt(dx*dx+dy*dy);

    alpha = atan2(dy,dx);


    ang = alpha-theta_robot;
    while(ang<-PI)
        ang+=2*PI;
    while(ang>=PI)
        ang-=2*PI;

    ang*=K_TH;
    lin=linear_speed_;

    if(reversed_)
    {
        if(ang>0)
            ang=PI-ang;
        else if(ang<0)
            ang=-PI-ang;
        lin*=-1;
    }

    if(ang>ANGULAR_SPEED_MAX)
    {
    	ang = ANGULAR_SPEED_MAX;
    	lin*=0.2;
    }
    else if(ang < (- ANGULAR_SPEED_MAX) )
    {
    	ang = -ANGULAR_SPEED_MAX;
    	lin*=0.2;
    }

    if(lin>LINEAR_SPEED_MAX)
	{
		lin = LINEAR_SPEED_MAX;
	}
	else if(lin < (- LINEAR_SPEED_MAX) )
	{
		lin = -LINEAR_SPEED_MAX;
	}




}





void PathFollower::computeLastPointAngleCmd(double &lin, double &ang)
{
    tf::StampedTransform tf_robot;

    try
    {
        //TODO: replace "map" by path.header.frame_id
        tf_listener_.lookupTransform("/map", "base_link", ros::Time(0), tf_robot);
    }
    catch (tf::TransformException ex)
    {
        ROS_ERROR("%s",ex.what());
        ros::Duration(1.0).sleep();
        return;
    }

    double theta_robot;
    double theta_des;

    theta_robot = tf::getYaw(tf_robot.getRotation());
    theta_des = tf::getYaw(path_.poses[index_path_].orientation);
    dth_ = theta_des-theta_robot;
    while(ang<-PI)
        dth_+=2*PI;
    while(ang>=PI)
        dth_-=2*PI;

    ang = dth_;
    ang*=K_TH;
    if(ang>ANGULAR_SPEED_MAX)
        ang = ANGULAR_SPEED_MAX;
    else if(ang < (- ANGULAR_SPEED_MAX) )
        ang = -ANGULAR_SPEED_MAX;

    lin=0.0;
}


void PathFollower::publishRatio()
{
	double ratio_to_next = (du_ - NEXT_POINT_DISTANCE_THRESH) / (first_du_ - NEXT_POINT_DISTANCE_THRESH);

	scenario_msgs::PathFeedback pathFeedback;
	pathFeedback.uid = path_uid_;
	pathFeedback.ratio = (1.0*index_path_ + (1-ratio_to_next))/size_path_;
	ratio_pub_.publish(pathFeedback);
}


void PathFollower::spinOnce()
{
	geometry_msgs::Twist cmd;
    cmd.linear.y=0;
    cmd.linear.z=0;
    cmd.angular.x=0;
    cmd.angular.y=0;

    if(size_path_ > 0 && index_path_<size_path_)
    {
        if(index_path_ == size_path_-1)
        {
            if(du_ > LAST_POINT_DISTANCE_THRESH)
            {
                computeCmd(cmd.linear.x, cmd.angular.z);
                cmd_pub_.publish(cmd);
            }
            else if(dth_ > LAST_POINT_ANGLE_THRESH)
            {
                computeLastPointAngleCmd(cmd.linear.x, cmd.angular.z);
                cmd_pub_.publish(cmd);
            }
            else
            {
                index_path_++;
                du_=INIT_DU;
                dth_ = PI;
                ROS_INFO_STREAM("Heading to point #"<<index_path_<<"/"<<size_path_<<" : ("
                                        <<path_.poses[index_path_].position.x<<"|"<<path_.poses[index_path_].position.y<<")");
            }
        }
        else
        {
            if( du_ > NEXT_POINT_DISTANCE_THRESH)
            {
                computeCmd(cmd.linear.x, cmd.angular.z);
                cmd_pub_.publish(cmd);
            }
            else
            {
                index_path_++;
                du_=INIT_DU;
                dth_ = PI;
            }
        }
    }
    else if(size_path_ > 0 && index_path_==size_path_)
    {
        cmd.linear.x = 0;
        cmd.angular.z = 0;
        cmd_pub_.publish(cmd);
        size_path_=-1;

		ROS_INFO_STREAM("Path follower ended");
    }
    else if(size_path_ ==0)
    {
        cmd.linear.x = 0;
        cmd.angular.z = 0;
        cmd_pub_.publish(cmd);
        size_path_=-1;

		ROS_INFO_STREAM("Path follower received 0 sized path");
    }

    // publish ratio
	if(cpt_>RATIO_PUBLISH_RATE_DIVIDOR)
	{
		publishRatio();
		cpt_=0;
	}
    cpt_++;
}


int main(int argc, char** argv)
{
	ros::init(argc, argv, "path_follower_node");
	ros::NodeHandle nh;
	PathFollower pf(nh);
	ros::Subscriber path_sub = nh.subscribe("path", 1, &PathFollower::pathCB, &pf);
	ros::Rate loop(LOOP_RATE);

	while(ros::ok())
	{
		pf.spinOnce();
		ros::spinOnce();
		loop.sleep();
	}

    return 0;
}
