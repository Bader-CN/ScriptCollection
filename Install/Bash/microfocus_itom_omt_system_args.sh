#!/bin/bash
#################################################################
#   author: zhanghong.personal@outlook.com
#  version: 1.1
#    usage: microfocus_itom_omt_system_args.sh
# describe: Auto adjust system parameters to meet OMT(OPTIC Management Toolkit) installation conditions
#
# release nodes:
#   2022.12.03 - first release
#   2023.01.03 - add AlmaLinux 8.x / change comment
#################################################################

# Global
os_type="Others"

# Check OS & Settings
function check_os_settings() {
    # check OS hostname
    hostname=`hostname -f`
    check_hostname=$(echo $hostname | grep -E \\w+\.\\w+\.\\w+)
    if [[ $check_hostname != "" ]]
    then
        message="`date -u` check_os_settings [INFO] hostname is OK"
        echo $message
    else
        message="`date -u` check_os_settings [ERROR] hostname should must be FQDN format, For example: hostname.domain.com"
        echo $message
        exit 1
    fi
    # check OS version
    if [[ `cat /etc/redhat-release | grep -E 'RedHat.*7\.[6-9]|CentOS.*7\.[6-9]'` != "" ]]
    then
        os_type="RHEL7"
        message="`date -u` check_os_settings [INFO] OS is RHEL 7/ CentOS 7"
        echo $message

    elif [[ `cat /etc/redhat-release | grep -E 'RedHat.*8\.[1-9]|CentOS.*8\.[1-9]|Rocky.*8\.[1-9]|AlmaLinux.*8\.[1-9]'` != "" ]]
    then
        os_type="RHEL8"
        message="`date -u` check_os_settings [INFO] OS is RHEL 8 /CentOS 8 /Rocky Linux 8 /AlmaLinux 8"
        echo $message

    elif [[ $(os_type) == "Other" ]]
    then
        message="`date -u` check_os_settings [ERROR] OS is not support"
        echo $message
        exit 1
    fi
}

# disable ipv6 in /etc/hosts
function disable_hosts_ipv6() {
    # find ::1 from /etc/hosts
    localhost_ipv6=`cat /etc/hosts | grep -E ^::1`
    if [[ $localhost_ipv6 != "" ]]
    then
        # shellcheck disable=SC2091
        $(sed -i 's/^::1/#::1/' /etc/hosts)
        message="`date -u` disable_hosts_ipv6 [INFO] has disable ipv6 localhost resolution"
        echo $message
    fi
}

# change system parameters
function change_sys_args() {
    # install br_netfilter
    (modprobe br_netfilter)
    (echo "br_netfilter" > /etc/modules-load.d/br_netfilter.conf)

    # add kernal parameters
    if [[ $os_type == "RHEL7" ]]
    then
        cat > /etc/sysctl.conf << EOF
# for MicroFocus OMT
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
net.ipv4.tcp_tw_recycle = 0
fs.may_detach_mounts = 1
kernel.sem=50100 128256000 50100 2560
EOF
        message="`date -u` change_sys_args [INFO] change /etc/sysctl.conf parameters(/sbin/sysctl -p)"
        echo $message
        /sbin/sysctl -p

    elif [[ $os_type == "RHEL8" ]]
    then
        cat > /etc/sysctl.conf << EOF
# for MicroFocus OMT
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
kernel.sem=50100 128256000 50100 2560
EOF
        message="`date -u` change_sys_args [INFO] change /etc/sysctl.conf parameters(/sbin/sysctl -p)"
        echo $message
        /sbin/sysctl -p
    fi
}

# yum install packages
function yum_install_packages() {
    message="`date -u` yum_install_packages [INFO] will yum install packages"
    echo $message

    if [[ $os_type == "RHEL7" ]]
    then
        yum install device-mapper-libs java-1.8.0-openjdk libgcrypt libseccomp libtool-ltdl net-tools nfs-utils rpcbind \
        systemd-libs unzip conntrack-tools curl lvm2 httpd-tools checkpolicy policycoreutils policycoreutils-python \
        container-selinux socat m4 lsof chrony bind-utils system-storage-manager zip -y

    elif [[ $os_type == "RHEL8" ]]
    then
        yum install device-mapper-libs java-1.8.0-openjdk libgcrypt libseccomp libtool-ltdl net-tools nfs-utils rpcbind \
        systemd-libs unzip conntrack-tools curl lvm2 httpd-tools checkpolicy policycoreutils policycoreutils-python-utils \
        container-selinux socat m4 lsof chrony bind-utils system-storage-manager zip -y
    fi
}

# Main Processing
check_os_settings
disable_hosts_ipv6
change_sys_args
yum_install_packages

# disable firewalld
systemctl disable firewalld
systemctl stop firewalld

# Finish Info
echo "`date -u` FinishInfo [INFO] parameters are adjusted, please configure the following parameters as required"
echo -e "
\033[32m 1.Configuring the NFS, for example: \033[0m
    \033[34m# OpsB 2021.XX \033[0m
    cd OMT_Embedded_K8s_<version>/cdf/scripts
    ./setupNFS.sh /var/vols/itom/core true 1999 1999
    ./setupNFS.sh /var/vols/itom/db-single-vol true 1999 1999
    ./setupNFS.sh /var/vols/itom/db-backup-vol true 1999 1999
    ./setupNFS.sh /var/vols/itom/itom-logging-vol true 1999 1999
    ./setupNFS.sh /var/vols/itom/opsbvol1 true 1999 1999
    ./setupNFS.sh /var/vols/itom/opsbvol2 true 1999 1999
    ./setupNFS.sh /var/vols/itom/opsbvol3 true 1999 1999
    ./setupNFS.sh /var/vols/itom/opsbvol4 true 1999 1999
    ./setupNFS.sh /var/vols/itom/opsbvol5 true 1999 1999
    ./setupNFS.sh /var/vols/itom/opsbvol6 true 1999 1999
    ./setupNFS.sh /var/vols/itom/opsbvol7 true 1999 1999
    chmod -R 755 /var/vols/itom/core
    chmod -R 755 /var/vols/itom/db-single-vol
    chmod -R 755 /var/vols/itom/db-backup-vol
    chmod -R 755 /var/vols/itom/itom-logging-vol
    chmod -R 755 /var/vols/itom/opsbvol1
    chmod -R 755 /var/vols/itom/opsbvol2
    chmod -R 755 /var/vols/itom/opsbvol3
    chmod -R 755 /var/vols/itom/opsbvol4
    chmod -R 755 /var/vols/itom/opsbvol5
    chmod -R 755 /var/vols/itom/opsbvol6
    chmod -R 755 /var/vols/itom/opsbvol7

    \033[34m# OpsB 2022.XX \033[0m
    cd OMT_Embedded_K8s_<version>/cdf/scripts
    ./setupNFS.sh /var/vols/itom/data true 1999 1999
    ./setupNFS.sh /var/vols/itom/opsbvol1 true 1999 1999
    ./setupNFS.sh /var/vols/itom/opsbvol2 true 1999 1999
    ./setupNFS.sh /var/vols/itom/opsbvol3 true 1999 1999
    ./setupNFS.sh /var/vols/itom/opsbvol4 true 1999 1999
    ./setupNFS.sh /var/vols/itom/opsbvol5 true 1999 1999
    ./setupNFS.sh /var/vols/itom/opsbvol6 true 1999 1999
    ./setupNFS.sh /var/vols/itom/opsbvol7 true 1999 1999
    chmod -R 755 /var/vols/itom/data
    chmod -R 755 /var/vols/itom/opsbvol1
    chmod -R 755 /var/vols/itom/opsbvol2
    chmod -R 755 /var/vols/itom/opsbvol3
    chmod -R 755 /var/vols/itom/opsbvol4
    chmod -R 755 /var/vols/itom/opsbvol5
    chmod -R 755 /var/vols/itom/opsbvol6
    chmod -R 755 /var/vols/itom/opsbvol7

\033[32m 2.Configuring k8s PVs if you need COSO \033[0m
    dd if=/dev/zero of=/var/opt/vol1 bs=1G count=20
    dd if=/dev/zero of=/var/opt/vol2 bs=1G count=20
    dd if=/dev/zero of=/var/opt/vol3 bs=1G count=20
    mkfs.ext4 -F /var/opt/vol1
    mkfs.ext4 -F /var/opt/vol2
    mkfs.ext4 -F /var/opt/vol3
    mkdir -p /mnt/disks/lpv1
    mkdir -p /mnt/disks/lpv2
    mkdir -p /mnt/disks/lpv3
    mount /var/opt/vol1 /mnt/disks/lpv1
    mount /var/opt/vol2 /mnt/disks/lpv2
    mount /var/opt/vol3 /mnt/disks/lpv3

    \033[34m# Edit the /etc/fstab and add entries for the new file-based filesystems \033[0m
    \033[34m# Check /etc/fstab can use command: df -h |grep -E 'Filesystem|lpv \033[0m
    /var/opt/vol1 /mnt/disks/lpv1 ext4 defaults
    /var/opt/vol2 /mnt/disks/lpv2 ext4 defaults
    /var/opt/vol3 /mnt/disks/lpv3 ext4 defaults

    \033[34m# Edit permission \033[0m
    chown -R 1999:1999 /mnt/disks/*; chmod -R 755 /mnt/disks; ls -la /mnt/disks

\033[32m 3.Install ITOM OMT \033[0m
    \033[34m# CDF 2021.XX \033[0m
    ./install --nfs-server <nfs_server> --nfs-folder /var/vols/itom/core -c config.json
    \033[34m# CDF 2022.XX \033[0m
    ./install -c <abs_path_config.json> --nfsprov-server <nfs_server> --nfsprov-folder /var/vols/itom/data --capabilities NfsProvisioner=true"