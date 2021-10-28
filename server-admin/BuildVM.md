# Setting up a VM

Request VM from IS without OS.
Install minimal CentOS8. 
Download ISO image. To access install media from CDrom
```
mkdir /media/CentOS
mount /dev/cdrom /media/CentOS
yum --disablerepo=* --enablerepo=c7-media  yum-command
```
The VM options menu has an option to switch to BIOS setup next time the VM boots.

So far IS have set up the DNS entries for VMs in advance but you need 
to configure the parameters manually during install. 

For the default IS service LAN
```
netmask 255.255.254.0
gateway 129.215.11.254
DNS entries 129.215.205.191, 129.215.70.239, 129.215.168.3
```

The VM infrastructure applies default firewalling so you need to request 
ports be opened when requesting the machine.
Firewalls are using `firewalld`.

To enable Apache:
```
yum install httpd
firewall-cmd --zone=public --add-service=http --permanent
firewall-cmd --reload

systemctl enable httpd
systemctl start httpd
```

For https you also need
```
yum install mod_ssl 
firewall-cmd --zone=public --add-service=https --permanent
```

For automatic patching see
https://linuxaria.com/howto/enabling-automatic-updates-in-centos-7-and-rhel-7

## EASE Kerberos with CentOS 8

Follow the instructions here how to request a certificate and how to 
configure Apache:
https://www.wiki.ed.ac.uk/display/EASE/Advanced+Help

pam_krb5 was deprecated and is not available in the CentOS 8 package 
repositories, instead SSSD is recommended.
Install the Security System Services Daemon (SSSD) and Kerberos:

```
yum install sssd
yum install krb5-workstation
```

Create `/etc/sssd/sssd.conf`:
```
[sssd]
services = nss, pam
domains = EASE.ED.AC.UK
 
[domain/EASE.ED.AC.UK] 
id_provider = files
auth_provider = krb5
krb5_realm = EASE.ED.AC.UK
krb5_server = kadmin.ease.ed.ac.uk
```

Change permissions
```
chmod 600 /etc/sssd/sssd.conf
```
Create `/etc/krb5.conf`:
```
includedir /etc/krb5.conf.d/
 
[libdefaults]
        # allow_weak_crypto = true is needed until we phase out single DES
        allow_weak_crypto = true
        default_realm = EASE.ED.AC.UK
        clockskew = 300
        noaddresses = true
        dns_fallback = true
        forwardable = true
 
# Uncomment the lines below if you want to enable cross-realm authentication
# between the Active Directory realm (ED.AC.UK), the School of Informatics
# realm (INF.ED.AC.UK) and the EASE realm (EASE.ED.AC.UK)
#[capaths]
#        EASE.ED.AC.UK = {
#                INF.ED.AC.UK = .
#                ED.AC.UK = .
#        }
#        INF.EASE.ED.AC.UK = {
#                EASE.ED.AC.UK = .
#        }
#        ED.AC.UK = {
#                EASE.ED.AC.UK = .
#        }
 
[realms]
        EASE.ED.AC.UK = {
                admin_server = kadmin.ease.ed.ac.uk
                # Uncomment these lines if you don't want to use the DNS
                # to locate the KDCs
                kdc = kerberos.ease.ed.ac.uk
                kdc = kerberos-1.ease.ed.ac.uk
                # Uncomment these lines if you want to enable a default mapping
                # of principals from the AD realm and Informatics realms
                #auth_to_local = RULE:[1:$1@$0](.*@ED\.AC\.UK)s/@.*//
                #auth_to_local = RULE:[1:$1@$0](.*@INF\.ED\.AC\.UK)s/@.*//
                #auth_to_local = DEFAULT
        }
        INF.ED.AC.UK = {
                # Uncomment these lines if you want to enable a default mapping
                # of principals from the EASE and AD realms to Informatics
                # auth_to_local = RULE:[1:$1@$0](.*@EASE\.ED\.AC\.UK)s/@.*//
                # auth_to_local = DEFAULT
        }
        ED.AC.UK = {
                # Uncomment these lines if you want to enable a default mapping
                # of principals from the EASE realm to AD
                # auth_to_local = RULE:[1:$1@$0](.*@EASE\.ED\.AC\.UK)s/@.*//
                # auth_to_local = DEFAULT
        }
```

Restart or start SSSD:
```
systemctl restart sssd
```

## Add users to the system:
```
useradd -m -u <uid> -G wheel <uun>
```
This is using university default uid (not sure where to look that up).

You can check the EASE authentication is working using:
```
kinit user  # For the user that you have just added - you will need to know the EASE password so this best be yourself
klist       # To check that a kerberos ticket has been added
```

## Configure Apache

Add the following to `/etc/httpd/conf/httpd.conf`:

Load Cosign module
```
LoadModule cosign_module  modules/mod_cosign.so
```

Enable http -> https redirect
```
RewriteEngine On
RewriteCond %{HTTPS} !=on
RewriteRule ^/?(.*) https://%{SERVER_NAME}/$1 [R,L]
```
Copy the httpd config files for the OpportunityMatch WSGI and 
to enable EASE protection.