#!/bin/bash
#################################################################
#   author: zhanghong.personal@outlook.com
#  version: 1.0
#    usage: service_check.sh <service_name>
# describe: Check whether the specified service has been started. 
#           If not, script will try start service.
#
# release nodes:
#   2022.06.14 - first release
#   2023.01.30 - change file format CRLF -> LF
#################################################################

# User variables
num_try=5				# number of maximum retry
numslep=10				# delay of starting the service for the first time (seconds)
numwait=30				# recheck time after service command start (seconds)
num_start_delay=5		# after the script starts, the delay is checked for how many seconds
num_wait_delay=60		# if service is starting or stopping, will wait the specified time (seconds)

# Internal variables
svrname=$1
logfile=/var/log/messages
section="Service.Bash.service_check"

# RedHat/CentOS/Rocky Linux 7.x or 8.x
os_redhat=`cat /etc/redhat-release | grep -E "Red Hat Enterprise Linux.*release [78]|CentOS Linux.*release [78]|Rocky Linux.*release 8" | wc -l`
redhat_status="systemctl status"
redhat_start="systemctl start"

if [ "$os_redhat" -eq 1 ]; then
  # script startup delay
	sleep $num_start_delay

	# check service status - starting or stopping
	service_staing=`sudo -S $redhat_status $svrname | grep -E "activating \(start\)|deactivating \(stop\)" | wc -l`
	if [ "$service_staing" -eq 1 ]; then
	  wait_try_num=1
	  while [ "$service_staing" -eq 1 -a $wait_try_num -le $num_try ];
	  do
	    message="`date -u` `hostname -s` $section [INFO] $svrname is starting or stopping, script will waiting $num_wait_delay seconds"
	    echo $message
	    echo $message >> $logfile
	    sleep $num_wait_delay
	    wait_try_num=`expr $wait_try_num + 1`
	    service_staing=`sudo -S $redhat_status $svrname | grep -E "activating \(start\)|deactivating \(stop\)" | wc -l`
	  done
	fi

	# check service status - stop
  service_status=`sudo -S $redhat_status $svrname | grep -E "inactive \(dead\)" | wc -l`
	if [ "$service_status" -eq 1 ]; then
	  # try start service
		sleep $numslep
		start_try_num=1
		while [ $service_status == 1 -a $start_try_num -le $num_try ]
		do
			message="`date -u` `hostname -s` $section [INFO] try starting $svrname, try number: $start_try_num"
			echo $message
			`sudo -S $redhat_start $svrname`
			echo $message >> $logfile
			start_try_num=`expr $start_try_num + 1`
			sleep $numwait
			service_status=`sudo -S $redhat_status $svrname | grep -E "inactive \(dead\)|activating \(start\)|deactivating \(stop\)" | wc -l`
			
			if [ "$service_status" -eq 0 ]; then
				message="`date -u` `hostname -s` $section [INFO] service $svrname successful startup"
				echo $message
				echo $message >> $logfile
			else
				message="`date -u` `hostname -s` $section [WARN] service $svrname is stop/starting/stopping, try number: $start_try_num"
				echo $message
				echo $message >> $logfile
			fi        		
		done

	else
		message="`date -u` `hostname -s` $section [INFO] service $svrname had be start, script will logout"
		echo $message
		echo $message >> $logfile
    fi

else
    # OS not support
    echo "`date -u` `hostname -s` $section [ERROR] OS type or version is not support!"
fi