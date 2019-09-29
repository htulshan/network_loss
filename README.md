# network_loss
Motivation:
Issues related to sporadic network outages can be difficult to troubleshoot specially when the issue happens once every 24 hours etc since in some cases only outputs at the exact time of issue would be required to isolate the problem.

Objective:
To monitor the network for an outage and take relevant outputs from the devices in question to isolate the issue as much as possible
The script solves the following problems.
1) It constantly monitors the network for a specific trigger condition. ( In this script a ping drop between a specific source and destination)
2) In case the trigger condition is satified it ( in this case a ping drop )will try to find the point of failure and collect outputs from the network device which might have dropped the packet.


Script logic to achieve the objective:
1) The script will run a controlled continious ICMP from the source to the destination. 
2) In case there is a ping drop it will trigger a traceroute from the source to the destination.
3) Using the expected traceroute and comparing it with the traceroute result obtained at the time of issue we can find the last visible hop and the hop next to that.
4) Logging into the devices mentioned in point 3 and taking show command outputs.

Assuptions:
1) We have SSH enabled on all the network devices from source to destination.
2) We are allowing ICMP on the path from source to destination
3) We have allowed traceroute from source to destination.
4) We are hosting the script on windows end host.
5) We have a common login ID and password and enable secret password on all the devices from source to destination.
6) The end device on which we will run this script should be allowed to login into all the network devices from source to destination using the IPs in the path.
(if any of the above assumption does not fit in your network deployment, appropriate changes might be required in the script)

How to use the script:
1) The script has been tested on windows 8,10 platform. If we want to run it on some other operating system appropriate changes in the script might be required.
2) Reachability to the destination can be tested from the local host on which we are hosting the script or we can login into a remote network device (switch, router etc) and use it as the source to check rechabilty to the destination IP.
3) The expected traceroute result needs to be stored in a .csv file along the fireware type as per netmiko module  ( use device_type as "host" if the device cannot be logged into using netmiko)
4) Appropriate input needs to be provided to the script at run time, once all the inputs have been given the script will run and provide you the ouptuts in case of any packet loss from source to destination.
5) The script also saves the output to a text file named : scriptoutput.
