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
s.bind(address)

# Wait for client
while True:
    print('Waiting for client...')
    data, addr_c = s.recvfrom(1024)
    if data.decode() == 'server?':
        print('Conneted to client at '+str(addr_c))
        s.sendto('yes'.encode(),addr_c)
        break

def callback(data):
    msg_json = json_message_converter.convert_ros_message_to_json(data)
    msg_json = msg_json.encode()
    pkg_len = len(msg_json)
    pkg_num = pkg_len//pkg_div_len
    if len(msg_json)%pkg_div_len != 0:
        pkg_num += 1
    # Send start msg
    #rospy.loginfo('New pkg len=%d'%pkg_num)
    s.sendto(str(pkg_num).encode(),addr_c)
    s.recv(1024)#for ack
    # loop
    for i in range(pkg_num):
        temp = msg_json[i*pkg_div_len : min((i+1)*pkg_div_len, pkg_len)]
        s.sendto(temp,addr_c)
        #print('   sent num:%d'%i)
        #if i%3 == 0:
        #if i == pkg_num-1 :
        #    s.recv(3)
    #rospy.loginfo(' done.')

# Launch ros node and subscriber
rospy.init_node('udp_serv_send')
rospy.Subscriber('/hires/image_raw', Image, callback)
rospy.spin()
