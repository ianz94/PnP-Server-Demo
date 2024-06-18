## Intro
This is a Cisco PnP server written in Python Flask, which runs HTTP services and makes use of the Cisco PnP protocol to provision Cisco IOS-XE devices automatically.

This project is developed specially for ISR1k routers, which by default do not have Guestshell equipped, thus cannot run ZTP Python scripts. This PnP Server is able to:
 - Update device day-0 configuration
 - Upgrade and run new image
 - Transfer a generic file (e.g. Guestshell tarball) from server onto device bootflash

Please glance through [this post](https://developer.cisco.com/site/open-plug-n-play/learn/learn-open-pnp-protocol/) to get a brief idea of PnP protocol before you move on.

## PnP Workflow
With PnP server and DHCP server being set up properly, we can achieve such workflow automatically:

 1. New ISR1k boots up, it will broadcast a [*DHCP Discover*](https://en.wikipedia.org/wiki/Dynamic_Host_Configuration_Protocol#Operation) message, trying to get an IP address. The *DHCP Discover* message contains string "ciscopnp" in option 60, and device PID (for example "C1131-8PWB") in option 124.
 2. The DHCP server should have been previously configured to identify  “ciscopnp” in Option 60 and device PID in option 124. It will respond a *DHCP Offer* message, with the PnP server IP address hardcoded in option 43.
 3. If no startup-config is present in NVRAM, the device will enter PnP workflow and connect to the PnP server
 4. PnP server sends CLI to set the config-register value of device (for ISR1k should be 0x2102)
 5. PnP server sends the day0 config to ISR1k
 6. PnP server sends CLI “_write memory_” to ISR1k, so its day0
    running-config gets copied into startup-config
 7. PnP server sends the new IOS image to ISR1k, ISR1k copies it into
    Bootflash
 8. ISR1k automatically reloads itself. And then boots up with the new
    image. Day0 config is running well.
 9. PnP server then transfer the Guestshell tarball (or any other generic file) to the device bootflash. User can install it and get back the Guestshell funtionality later.

Please note this is a run-to-completion model. No need for users to interfere. All you need to do is to boot up the ISR1k device, sit down and wait.  Please make sure the ISR1k device boots up with no start-up config, otherwise the PnP workflow won't kick in.

## Configuration Steps
### Step 1
Choose the server pod in your environment to host the PnP services. This will be our PnP server. It should be in the same subnet with the ISR1k devices so it is reachable by them. Find out the IP address of our PnP server. (In this example it is *10.2.3.4*).
### Step 2
Configure the DHCP server. Make sure it is able to identify string "ciscopnp" in option 60, and string "C11" in option 124 of a DHCP message, and will respond with PnP server address in option 43. In our example here, option 43 will be "5A;B2;K4;I10.2.3.4;J80".
Syntax explanation:
```
"5A;B2;K4;I10.24.67.108;J80"
5 – DHCP type code 5
A – Active feature operation code
B2 – PnP server IP address type is IPv4
I10.2.3.4 – PnP server IP address
J80 – Port number 80 (use HTTP service)
```
If you are using a Linux server (especially Ubuntu) as the DHCP server in your environment, one way to achieve this is to run `sudo vim /etc/dhcp/dhcpd.conf` , and add these lines of code to the *dhcpd.conf* file:
```
option space CISCO_PNP;
option CISCO_PNP.pnpserver code 43 = string;
option ClientPID code 124 = string;
class "ciscopnp-isr1k" {
match if option vendor-class-identifier = "ciscopnp" and substring(option ClientPID, 6, 3) = "C11";
vendor-option-space CISCO_PNP;
option CISCO_PNP.pnpserver "5A;B2;K4;I10.2.3.4;J80";
}
```
By identifying "C11" in device PID, the DHCP server will send the PnP server IP address to ISR1k devices ONLY, other types of devices (ISR4k, CAT9k etc) are NOT affected. They will not get such option 43, and will still follow their own provisioning workflow (ZTP etc).

Again, please remember to change *10.2.3.4* in the code above to your PnP server address.

Then save the *dhcpd.conf* file, restart the DHCP service, and check if it is actively running:
```
$ sudo systemctl restart isc-dhcp-server

$ sudo systemctl status isc-dhcp-server
```

### Step 3
Git clone this repo into the PnP server. 

Edit *pnp_env.py* to set up the environment variables (server IP address, config file name, name of the file you want to transfer etc).

Then please
 1. Put the image file you want the devices to upgrade with to the ./images folder, 
 2. Put the config files to the ./configs folder. Name the config file with device serial number, e.g. 'FGL2548L0AW.cfg'. Then each device will fetch its own config. However if it cannot find a .cfg named by its own serial number, it will simply fetch the default.cfg in ./configs folder. So make sure you edit the default.cfg to match your needs.
 3. Put the file which you want to transfer under ./files folder, for example *guestshell.17.09.01a.tar*.

### Step 4
Now you should be ready to go. Run the main script:

     $ python3 ./pnp_main.py

You should be able to see this output in your console. Please double check if the IP address and directories are correct. Otherwise the devices are not able to get what they want.
```
Running PnP server. Stop with ctrl+c

Bind to IP-address      : 10.2.3.4
Listen on port          : 80
Image file(s) base URL  : http://10.2.3.4/images
Config file(s) base URL : http://10.2.3.4/configs

 * Serving Flask app 'pnp_main'
 * Debug mode: off
```
Then boot up all the ISR1k devices. Please make sure they are either new devices or  have been factory-reset. They will not enter the PnP workflow if startup-config exists.

When the PnP server is running, you can cat the *DEVICE_STATUS.csv* to know about the current status. It should look like this:
```
$ cat DEVICE_STATUS.csv
 Serial Number |    Platform    | HW rev. |   IP Address   |       First Seen       |      Last Contact      |   Current Version    |              Target Image              | Config Update | File Transfer |    Device State    
  FGL2548L0AW  |   C1131-8PWB   |   V01   | 10.75.221.155  |  2024-06-18T14:42:28   |  2024-06-18T14:45:56   | 17.7.20210919:235108 |  c1100-universalk9.17.14.01a.SPA.bin   |     Done      |    Not yet    | UPGRADE_INPROGRESS 
  FDO2637M02M  |   C1131-8PWB   |   V01   | 10.75.221.156  |  2024-06-18T14:42:30   |  2024-06-18T14:46:26   | 17.7.20210919:235108 |  c1100-universalk9.17.14.01a.SPA.bin   |     Done      |    Not yet    | UPGRADE_INPROGRESS 
```
The ISR1k image file is 700+MB, the entire workflow should take some time.

If you see "FINISHED" in the last column, then this device have finished all 9 steps in the PnP workflow mentioned above.

Detailed log file can be found at *logs/pnp_debug.log*.