#intermittentconnectivityloss
import netmiko
import subprocess
from getpass import getpass
import time
import csv

class IntermittentConnectivityLoss():
	
	def login(self, devicedata):
		#to login into devices
		
		print('='*60)
		print(f"logging into the {devicedata['ip']} device now.")
		device = netmiko.ConnectHandler(**devicedata)
		if devicedata["secret"]: device.enable()
		print("Device has been logged into.")
		print("="*60)
		
		return device


	def trigger(self, dstip, device = {}):
		#to run ping to the destination and check if the ping drops
		count = 0
		currenttime = time.time()
		if device:
			while True:
				response = device.send_command(f"ping {dstip} repeat 1")
				print(response)
				count += 1
				print(f"ping count = {count}")
				time.sleep(1)
				
				#you can change the trigger condition according to your source device.
				if "Success rate is 0" in response:
					print('='*60)
					print("Destination is unrechable from source")
					print(f"Time elapsed since ping start = {time.time() - currenttime}s.")
					break
		
		else:
			while True:
				response = subprocess.run(f"ping -n 1 {dstip}", stdout = subprocess.PIPE, encoding = 'utf-8')
				print(response.stdout)
				count += 1
				print(f"ping count = {count}")
				time.sleep(1)
				
				if "Approximate round trip times in milli-seconds" not in response.stdout:
					print('='*60)
					print("Destination is unrechable from source")
					print(f"Time elapsed since ping start = {time.time() - currenttime}s.")
					break

		
	def trace_dst(self, device, dstip, sourceip, hops):
		#to trace to the destination
		
		currenttime = time.time()
		if device:
			
			#for extended ping on cisco device.
			tracenondefault = {
				'Target IP': dstip,
				'Source address': "",
				'Numeric display': 'yes',
				'Timeout': '1',
				'Probe': '1',
				'Maximum Time': hops
				}
			   
			response = device.send_command('traceroute', expect_string = r':')
			
			while True:
			
				if "Tracing the route" in response: break
				foundkey = False
				
				for key in tracenondefault.keys():
					
					if key in response:
						response = device.send_command(tracenondefault[key], expect_string = r':')
						foundkey = True
						break


				if "Verbose" in response:
					response = device.send_command("", expect_string = r"#")
					 
					
				elif not foundkey:
					response = device.send_command("", expect_string = r':')


		else:
			#if the source of network connectivity check is local machine
			response = subprocess.run(f"tracert -w 1 -d -h {hops} {dstip}", stdout=subprocess.PIPE, encoding='utf-8')
			return(response.stdout)

		print(f"Time taken to run traceroute {time.time() - currenttime}s")
		
		
		return(response)

	def problem_devices(self, device_list, traceroute):
		#to extrace the details of last hop device from traceroute
		
		#if the trace fails on first hop
		if device_list[0]['ip'] not in traceroute:
			return [device_list[0]]
		
		#if the trace fails on last hop
		elif traceroute.count(device_list[-1]['ip']) == 2:
			return [device_list[-1]]
			
		#if the trace fails on any hop between first and last hop
		else:
			temp = {}
			temp1 = {}
			for i in device_list:
				if i['ip'] in traceroute and i['ip'] != device_list[-1]['ip']:
					temp = i
					continue
				else:
					break
			return [temp, i]
			
	def collect_output(self, device, commands):
		#to collect outputs from last hop devices.
		
		print('='*60)
		print('Collecting output.')
		response = "\n".join(map(lambda x: "\n#{}\n{}".format(x, device.send_command(x)), commands))   
		return response

	def main(self):
		

		#collecting source and destination IP        
		print('='*60)
		print("Enter the IP details for source and destination.")
		print('='*60)
		sourceip = input("Enter the source IP : ")
		dstip = input("Enter the destination IP: ")
		hops = "" #default value of hops as per source IP platform.
		hops = input("The the number of hops between the source and destination: ")
		srcdevicedata = {} #source device netmiko data
		sourcedev = {} # #source device netmiko object
		commands = [] #command set to run on last hop devices


		#to collect expected traceresult
		print('='*60)
		tracedevice = input("Enter the list of expceted path as csv file: ")
		input_file = list(csv.DictReader(open(tracedevice)))
		print('='*60)
		
		
		#to collect show commands to be executed on last hop devices
		print("Enter the commands you want to collect from last hop devices(Enter 'OK' when done): ")
		while True:
			command = input("> ")
			if command != 'OK': commands.append(command)
			else: break 
		print("="*60)
		
		
		#to collect login details of network devices
		print("Enter login credentials for network devices.")
		username = input("Enter the username for devices: ")
		password = getpass("Enter the login password for devices: ")
		secret = getpass("Enter the enable secret for devices(press return if non is configured): ")


		#to check if we have to run the connectivity test from local host or a remote network device
		print('='*60)
		sourcedevcheck = input("Is the source IP on LOCALHOST or REMOTEHOST : ")
		if sourcedevcheck != 'LOCALHOST':
			print('='*60)
			print("Enter the details of source network device.")
			inputmethod = input("Do you want to use telnet or SSH to log into the source device : ")
			srcdevicedata['device_type'] = 'cisco_ios' if inputmethod.lower() == "ssh" else 'cisco_ios_telnet'
			srcdevicedata['ip'] = input("Enter the IP of source device for login : ")
			srcdevicedata['username'] = username
			srcdevicedata['password'] = password
			srcdevicedata['secret'] = secret
			
			
		#To check the input data before running the script 
		print('='*60)
		print('='*60)
		input("Verify all the input data and press return the run the script \nor type break sequence to abort the script and re run it.")
		print('='*60)
		print('='*60)
		
		#connecting to source network device.
		if sourcedevcheck != 'LOCALHOST':
			sourcedev = self.login(srcdevicedata)
		
		#to check for connectivity loss
		self.trigger(dstip, device = sourcedev)
		currenttime = time.time()
		
		with open('scriptoutput', 'w') as f: #file to save output result

			#taking output of traceroute at the time of ping drop
			print('='*60)
			print("Tracing to the destination from source")
			traceroute = self.trace_dst(sourcedev, dstip, sourceip, hops)
			print(traceroute)
			f.write(traceroute)
			
			#disconnecting from source device.
			if sourcedev:
				sourcedev.disconnect()
			
			#to collect the list of devices involved in packet drop last hop seen in traceroute and the next hop
			lasthopdevices = self.problem_devices(input_file, traceroute)
			
			
			#to collect output from last hop devices
			print('='*60)
			print("Collecting data from the last hop devices.")
			output = ""
			for devicedata in lasthopdevices:
				devicedata['username'] = username
				devicedata['password'] = password
				devicedata['secret'] = secret
				
				#to check if the device is reachable
				response = subprocess.run(f"ping -n 1 {devicedata['ip']}", stdout = subprocess.PIPE, encoding = 'utf-8')
				print(response.stdout)
				if "Approximate round trip times in milli-seconds" in response.stdout:
					#to check if the destination device is a not capable of connecting to remotely eg a host machine
					if devicedata['device_type'] != 'host': 
						device = self.login(devicedata)
						output += f"\n\n\nLogged into {devicedata['ip']} to collect outputs" 
						output += self.collect_output(device, commands)
						device.disconnect()
					else:
						print(f"'nDevice {devicedata['ip']} does not support remote connection.")
						output += f"\nDevice {devicedata['ip']} does not support remote connection."
				else: 
					print('='*60)
					print(f"\nDevice {devicedata['ip']} is unreachable")
					output += f"\n\nDevice {devicedata['ip']} is unreachable"
			
			#saveing output the file            
			f.write(output)
			print("Data saved to file")
		
		print(f"Time taken to collect outputs {time.time() - currenttime}s")
		input("Press return to exit")



if __name__ == "__main__":
	test = IntermittentConnectivityLoss()
	test.main()
	
