#include "path_follower.hpp"


PathFollower::PathFollower(ros::NodeHandle nh):
    nh_(nh),
    index_path_(0),
    size_path_(-1),
    du_(INIT_DU),
    dth_(PI),
    cpt_(0),
    linear_speed_(0.10),
    backward_(false),
    idle_(false),
    end_idle_time_(0.0)
{
    cmd_pub_   = nh_.advertise<geometry_msgs::Twist>("cmd_vel", 1);
    ratio_pub_ = nh_.advertise<scenario_msgs::PathFeedback>("path_feedback", 1);

    std::string tf_prefix;
    std::stringstream frame;

    if(nh_.getParam("tf_prefix", tf_prefix))
    {
        frame << tf_prefix <<"/base_link";
    }
    else
    {
        frame<<"/base_link";
    }
    robot_frame_ = frame.str();
    ROS_INFO_STREAM("frame robot in path follower : "<<frame.str());
}




void PathFollower::pathCB(const scenario_msgs::PathTravel &msg)
{
	path_uid_ = msg.uid;
    path_ = msg.path;
    time_at_poses_ = msg.time_at_poses;
    index_sequence_ = 0;
    index_path_ = 0;
    size_path_ = path_.poses.size();

    if(time_at_poses_.time_at_poses.size() == 0)
        linear_speed_= LINEAR_SPEED_DEFAULT ;
    if (size_path_ > 0)
	{
		ROS_INFO_STREAM("New path received :   id = " << path_uid_ << "  |  size = " << size_path_ << "  |  goal = "
						<< path_.poses.rbegin()->position.x << " ; " <<path_.poses.rbegin()->position.y
						<<"  |  elements in sequences = " << time_at_poses_.time_at_poses.size());
		goal_time_ = ros::Time::now() ;
	}
    else
    {
		ROS_INFO_STREAM("New path received :   id = " << path_uid_ << "  |  size = " << size_path_ << "  |  goal = ");
    }
}




void PathFollower::computeCmd(double &lin, double &ang)
{
    /***
     *Angular command can be improved with a PID...
     ***/
    double dx, dy, dth;
    double x_des, y_des;
    double delta_time;

    //get robot pose
    tf::StampedTransform tf_robot;
    try
    {
        tf_listener_.lookupTransform(path_.header.frame_id, robot_frame_, ros::Time(0), tf_robot);
    }
    catch (tf::TransformException ex)
    {
        ROS_ERROR("%s",ex.what());
        ros::Duration(1.0).sleep();
        return;
    }

    // compute distance and direction to next point
    dx = path_.poses[index_path_].position.x - tf_robot.getOrigin().x();
    dy = path_.poses[index_path_].position.y - tf_robot.getOrigin().y();
    if(du_ == INIT_DU)
        first_du_ = du_; //for feedback
    du_=sqrt(dx*dx+dy*dy);

    //dx = path_.poses[index_path_+1].position.x - tf_robot.getOrigin().x();
    //dy = path_.poses[index_path_+1].position.y - tf_robot.getOrigin().y();
    dth = atan2(dy,dx) - tf::getYaw(tf_robot.getRotation());
    while(dth<-PI)
        dth+=2.0*PI;
    while(dth>PI)
        dth-=2.0*PI;
    if(fabs(dth) < PI/6.0)
    {
        dth = tf::getYaw( path_.poses[index_path_].orientation) - tf::getYaw(tf_robot.getRotation());
        while(dth<-PI)
            dth+=2.0*PI;
        while(dth>PI)
            dth-=2.0*PI;
    }

    ROS_DEBUG_STREAM("du = "<< du_<< "  | dth " << dth);

    //backward angle
    if(backward_)
    {
        if(dth < 0.0)
            dth=PI-fabs(dth);
        else
            dth=-(PI-fabs(dth));
    }

    //compute speed
    /*
	if(goal_time_ < ros::Time::now())
	{
	    //in past --> no time set
	    lin = LINEAR_SPEED_DEFAULT;
	    if(backward_)
	        lin *= -1.0;
	}
	else
	{
	    delta_time =  (goal_time_ - ros::Time::now()).toSec();
        //computeAverageSpeed(time_at_poses_.time_at_poses[index_sequence_].pose_index, delta_time);
        lin=average_linear_speed_;
	}
	*/
	lin=average_linear_speed_;
    ROS_DEBUG_STREAM("Update speed to "<<lin<<" m/s. Time left : "<<delta_time<<"seconds.");

    // limitiation for average speed
    if(lin > 0.0 && lin > average_linear_speed_+0.10)
        lin = average_linear_speed_+0.10;
    else if(lin < 0.0 && lin < average_linear_speed_-0.10)
        lin = average_linear_speed_-0.10;

    // limitation for max speed
    if(lin > LINEAR_SPEED_MAX)
    {
		lin = LINEAR_SPEED_MAX;
		ROS_DEBUG("lin > SPEED MAX");
    }
	else if(lin < -LINEAR_SPEED_MAX)
	{
		lin = -LINEAR_SPEED_MAX;
		ROS_DEBUG("lin < SPEED MAX");
	}

    // limitation for dth

	if(fabs(dth) > ANGLE_THRESH_HIGH)
        lin*=0.01;
    else if(fabs(dth) > ANGLE_THRESH_LOW )
        lin*=0.10;
    //lin *=(1 - std::min( (dth*dth*dth*dth/2.0*PI), 1.0));
    // angular limitation
    ang = dth*K_TH*(1.0+fabs(lin));
    if(ang > ANGULAR_SPEED_MAX)
        ang = ANGULAR_SPEED_MAX;
    else if(ang < -ANGULAR_SPEED_MAX)
        ang = -ANGULAR_SPEED_MAX;
}





void PathFollower::computeLastPointAngleCmd(double &lin, double &ang)
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

    double theta_robot;
    double theta_des;

    theta_robot = tf::getYaw(tf_robot.getRotation());
    theta_des = tf::getYaw(path_.poses[index_path_].orientation);
    dth_ = theta_des-theta_robot;

    while(dth_<-PI)
        dth_+=2*PI;
    while(dth_>=PI)
        dth_-=2*PI;

    if(backward_)
    {
        if(dth_<0)
            dth_=PI-fabs(dth_);
        else
            dth_=-(PI-fabs(dth_));
    }

    ang = dth_*K_TH/2.0;
    if(ang > ANGULAR_SPEED_MAX)
        ang = ANGULAR_SPEED_MAX;
    else if(ang < -ANGULAR_SPEED_MAX)
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




float PathFollower::distanceToGoal(size_t index_goal)
{
    float distance = 0.0;
    for(size_t index = index_path_; index<index_goal; index++ )
    {
        distance += distanceBetweenPoints(index,index+1);
    }
    return distance;
}


float PathFollower::distanceBetweenPoints(size_t index1, size_t index2)
{
    float d, dx, dy;
    dx = path_.poses[index1].position.x - path_.poses[index2].position.x;
    dy = path_.poses[index1].position.y - path_.poses[index2].position.y;
    d = sqrt(dx*dx + dy*dy);
    return d;
}



void PathFollower::computeAverageSpeed(size_t index_goal, float time)
{
    if(time == 0.0)
    {
        ROS_WARN_STREAM("RECEIVED TIME NULL FOR NEXT GOAL IN THE CURRENT SEQUENCE");
        linear_speed_ = LINEAR_SPEED_DEFAULT;
        return;
    }
    float distance = distanceToGoal(index_goal);
    linear_speed_ = distance / time;
    ROS_INFO_STREAM("Linear speed  = "<<linear_speed_<<"   for distance/time : "<<distance<<" / "<<time<<" = "<< distance / time);

    if(fabs(linear_speed_) >= LINEAR_SPEED_MAX)
    {
        ROS_WARN_STREAM("Linear speed (asbolute) is too high : "<<linear_speed_<<" . Value set to max : "<<LINEAR_SPEED_MAX);
        linear_speed_ = LINEAR_SPEED_MAX;
    }
    else if(fabs(linear_speed_) >= float(LINEAR_SPEED_MAX/2.0))
    {
        ROS_WARN_STREAM("Linear speed (asbolute) is high : "<<linear_speed_<<" . May not be able to turn");
        //linear_speed_ = LINEAR_SPEED_MAX;
    }
    else
    {
        ROS_INFO_STREAM("Average linear speed for next goal : "<<linear_speed_);
    }
    if(backward_)
    {
        linear_speed_ *= -1;
        ROS_INFO("Going backward to next goal");
    }
    else
    {
        ROS_INFO("Going forward to next goal");
    }
}


void PathFollower::initNextGoal()
{

	//TODO : Enhancement : close loop due to time
    // For now : none working with a global time, seems to work when goal time
    // is define by section

    // set new time_goal
    float delta_time = time_at_poses_.time_at_poses[index_sequence_+1].time
                        - time_at_poses_.time_at_poses[index_sequence_].time;
    goal_time_ = ros::Time::now() + ros::Duration(delta_time);
    //goal_time_ += ros::Duration(delta_time);
    //delta_time = (goal_time_ - ros::Time::now()).toSec();

    //set backward value
    backward_ = time_at_poses_.time_at_poses[index_sequence_].backward;

    // compute average speed
    computeAverageSpeed(time_at_poses_.time_at_poses[index_sequence_+1].pose_index, (goal_time_ - ros::Time::now()).toSec());
    average_linear_speed_ = linear_speed_;
    ROS_INFO_STREAM("Next goal : pose : "<< time_at_poses_.time_at_poses[index_sequence_+1].pose_index
                    <<"  duration : "<<delta_time<<" seconds.");
    //check if idle
    if(time_at_poses_.time_at_poses[index_sequence_+1].pose_index==time_at_poses_.time_at_poses[index_sequence_].pose_index)
    {
        ROS_INFO_STREAM("Idle for "<<delta_time<<" seconds.");
        end_idle_time_ = goal_time_;
        idle_=true;
    }
    index_sequence_++;
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
        if(idle_)
        {
            cmd.linear.x = 0;
            cmd.angular.z = 0;
            cmd_pub_.publish(cmd);

            if(end_idle_time_ <= ros::Time::now())
                idle_ = false;
        }
        else
        {
            if( index_sequence_+1 <time_at_poses_.time_at_poses.size()
                    && index_path_ >= time_at_poses_.time_at_poses[index_sequence_].pose_index)
                initNextGoal();
            else if(index_path_ == size_path_-1)
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
    }
    else if(size_path_ > 0 && index_path_>=size_path_)
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
	ros::Subscriber path_sub = nh.subscribe("path_travel", 1, &PathFollower::pathCB, &pf);
	ros::Rate loop(LOOP_RATE);

	while(ros::ok())
	{
		pf.spinOnce();
		ros::spinOnce();
		loop.sleep();
	}

    return 0;
}
