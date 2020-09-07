#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import rospy
from std_msgs.msg import String
from sensor_msgs.msg import Image
import socket
import json_message_converter

# package protocal
# 
# Serv: Number of divided small pkgs (start msgs)
# Cli : ack
# loop: 
#       Serv: divided pkg
#       Cli:  ack 

pkg_div_len  = 60000
pkg_recv_len = pkg_div_len + 200

address = ('192.168.55.2', 12000)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Find Server
while True:
    s.sendto('server?'.encode(),address)
    print('Probing server...')
    s.settimeout(5.0)
    serv_ack = s.recv(1024).decode()
    if serv_ack == 'yes':
        print('Connected with server at'+str(address))
        break

# Launch ros node and publisher
pub = rospy.Publisher('cli_out', Image, queue_size=1)
rospy.init_node('udp_cli_rec')

while not rospy.is_shutdown():
    # wait for start msg:
    pkg_div_num = int(s.recv(1024).decode())
    if pkg_div_num > 0:
        #rospy.loginfo('New pkg len =%d'%pkg_div_num)
        pass
    else:
        rospy.loginfo('Error start msg, abort.')
        break
    s.sendto('ack'.encode(),address)
    # msg data init
    msg_json = bytearray(pkg_div_num*pkg_div_len)
    for i in range(pkg_div_num):
        msg_json[i*pkg_div_len:(i+1)*pkg_div_len] = s.recv(pkg_recv_len)
        #print('   rev num:%d'%i)
        #if i == pkg_div_num-1:
        #    s.sendto('a'.encode(),address)

    # trans to ros msg
    msg_ros = msg_json.decode()
    msg_ros = json_message_converter.convert_json_to_ros_message('sensor_msgs/Image', msg_json)
    pub.publish(msg_ros)
    #rospy.loginfo(' done.')
