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

addr_send = ('127.0.0.1', 12000)
s_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s_send.bind(addr_send)

addr_recv = ('127.0.0.1', 12001)
s_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s_recv.bind(addr_recv)

# Wait for client
while True:
    print('Waiting for client receiver...')
    data, addr_send_c = s_send.recvfrom(1024)
    if data.decode() == 'server?':
        print('  Conneted to client at '+str(addr_send_c))
        s_send.sendto('yes'.encode(),addr_send_c)
        break
while True:
    print('Waiting for client sender...')
    data, addr_recv_c = s_recv.recvfrom(1024)
    if data.decode() == 'server?':
        print('Conneted to client at '+str(addr_recv_c))
        s_recv.sendto('yes'.encode(),addr_recv_c)
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
    s_send.sendto(str(pkg_num).encode(),addr_send_c)
    s_send.recv(1024)#for ack
    # loop
    for i in range(pkg_num):
        temp = msg_json[i*pkg_div_len : min((i+1)*pkg_div_len, pkg_len)]
        s_send.sendto(temp,addr_send_c)
        #print('   sent num:%d'%i)
    #rospy.loginfo(' done.')

# Launch ros node and subscriber
rospy.init_node('udp_serv')
rospy.Subscriber('serv_in', Image, callback)
pub = rospy.Publisher('serv_out', Float32, queue_size=1)

while not rospy.is_shutdown():
    # wait for start msg:
    pkg_div_num = int(s_recv.recv(1024).decode())
    if pkg_div_num > 0:
        #rospy.loginfo('New pkg len =%d'%pkg_div_num)
        pass
    else:
        rospy.loginfo('Error start msg, abort.')
        break
    s_recv.sendto('ack'.encode(),addr_recv_c)
    # msg data init
    msg_json = bytearray(pkg_div_num*pkg_div_len)
    for i in range(pkg_div_num):
        msg_json[i*pkg_div_len:(i+1)*pkg_div_len] = s_recv.recv(pkg_recv_len)
        #print('   rev num:%d'%i)

    # trans to ros msg
    msg_json = msg_json.decode()
    msg_ros = json_message_converter.convert_json_to_ros_message('std_msgs/Float32', msg_json)
    pub.publish(msg_ros)
    #rospy.loginfo(' done.')
