#definition du message pour la communications des scenarios

#id du scenario
int32 uid

#timestamp pour le depart synchro des robots
time start_timestamp

#nom/path du scenario
string name

#type de scenario (choregraphic, travel, follow)
string type

#Liste des courbes de beziers
scenario_msgs/BezierPath bezier_paths

#Courbe recalculee
geometry_msgs/PoseArray checkedChoregraphicPath

#destination du scenario 
geometry_msgs/Pose2D target

#list of medias to display
scenario_msgs/MediaArray medias

#list of sequences
scenario_msgs/SequenceArray sequences
