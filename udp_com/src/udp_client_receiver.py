#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import rospy
from std_msgs.msg import Float32
from sensor_msgs.msg import Image
import socket
import json_message_converter

# package protocal
# 
# Serv: Number of divided small pkgs (start msgs)
# Cli : ack
# loop: 
#       Serv: divided pkg

pkg_div_len  = 60000
pkg_recv_len = pkg_div_len + 200

addr_recv = ('127.0.0.1', 12000)
s_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
addr_send = ('127.0.0.1', 12001)
s_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Find Server
while True:
    while True:
        s_recv.sendto('server?'.encode(),addr_recv)
        print('Probing receive server...')
        try:
            s_recv.settimeout(5.0)
            serv_ack = s_recv.recv(1024).decode()
        except socket.timeout:
            print('  Receive server port not found, retry...')
            continue
        break
    if serv_ack == 'yes':
        print('Connected with server at'+str(addr_recv))

    while True:
        s_send.sendto('server?'.encode(),addr_send)
        print('Probing send server...')
        try:
            s_send.settimeout(5.0)
            serv_ack = s_send.recv(1024).decode()
        except socket.timeout:
            print('  Send server port not found, retry...')
            continue
        break
    if serv_ack == 'yes':
        print('Connected with server at'+str(addr_send))
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
    s_send.sendto(str(pkg_num).encode(),addr_send)
    s_send.recv(1024)#for ack
    # loop
    for i in range(pkg_num):
        temp = msg_json[i*pkg_div_len : min((i+1)*pkg_div_len, pkg_len)]
        s_send.sendto(temp,addr_send)
        #print('   sent num:%d'%i)
    #rospy.loginfo(' done.')

# Launch ros node and publisher
rospy.init_node('udp_client')
rospy.Subscriber('cli_in', Float32, callback)
pub = rospy.Publisher('cli_out', Image, queue_size=1)

while not rospy.is_shutdown():
    # wait for start msg:
    pkg_div_num = int(s_recv.recv(1024).decode())
    if pkg_div_num > 0:
        #rospy.loginfo('New pkg len =%d'%pkg_div_num)
        pass
    else:
        rospy.loginfo('Error start msg, abort.')
        break
    s_recv.sendto('ack'.encode(),addr_recv)
    # msg data init
    msg_json = bytearray(pkg_div_num*pkg_div_len)
    for i in range(pkg_div_num):
        msg_json[i*pkg_div_len:(i+1)*pkg_div_len] = s_recv.recv(pkg_recv_len)
        #print('   rev num:%d'%i)

    # trans to ros msg
    msg_ros = msg_json.decode()
    msg_ros = json_message_converter.convert_json_to_ros_message('sensor_msgs/Image', msg_json)
    pub.publish(msg_ros)
    #rospy.loginfo(' done.')
