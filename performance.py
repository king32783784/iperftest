#!/usr/bin/env python
#coding=utf-8
import paramiko
import os
import subprocess
import string
import time
import datetime
import sys
import math
import re
import linecache
import multiprocessing
import threading
import Queue
import xml.dom.minidom
import logging

from ftplib import FTP
from optparse import OptionParser
from xml.dom import  minidom
try:
    import paramiko
except:
    os.system("python setup.py install")

reload(sys) 
sys.setdefaultencoding('utf-8')


class Parsing_XML():
    '''Parsing XML-formatted files for Lart_i'''
    def get_attrvalue(self,node, attrname):
        return node.getAttribute(attrname) if node else ''

    def get_nodevalue(self,node, index = 0):
        return node.childNodes[index].nodeValue if node else ''

    def get_xmlnode(self,node,name):
        return node.getElementsByTagName(name) if node else []

    def xml_to_string(self,filename):
        doc = minidom.parse(filename)
        return doc.toxml('UTF-8')

    def get_xml_data(self,filename):
        doc = minidom.parse(filename) 
        root = doc.documentElement
        ue_nodes = self.get_xmlnode(root,'ue')
        ue_list=[]
        for node in ue_nodes: 
            ue_id = self.get_attrvalue(node,'id') 
            node_clientip = self.get_xmlnode(node,'clientip')
            node_serverip = self.get_xmlnode(node, 'serverip')
            node_downfile = self.get_xmlnode(node,'downfile')
            node_localpath = self.get_xmlnode(node,'localpath')
            ue_clientip = self.get_nodevalue(node_clientip[0])
            ue_serverip = self.get_nodevalue(node_serverip[0])
            ue_downfile = self.get_nodevalue(node_downfile[0])
            ue_localpath = self.get_nodevalue(node_localpath[0]).encode('utf-8','ignore') 
            ue = {}
            ue['id'] , ue['clinetip'] , ue['serverip'], ue['downfile'] , ue['localpath'] = (
                ue_id, ue_clientip, ue_serverip, ue_downfile, ue_localpath)
            ue_list.append(ue)
        return ue_list

    @staticmethod
    def parsing_label_list(labelname, xmlfile):
        '''Parsing Gets the list labels'''
        try:
            xml_dom = xml.dom.minidom.parse(xmlfile)
            xml_label = xml_dom.getElementsByTagName(labelname)
        except IOError:
            print 'Failed to open %s file,Please check it' % xmlfile
            exit(1)
        xml_label_list = []
        for single_label in xml_label:
            xml_label_list.append(single_label.firstChild.data)
        return xml_label_list

    @staticmethod
    def specific_elements(labelname, xmlfile):
        '''Read the specific elements,call the class may need to override
           this function.By default returns a "xml_list" and "xml_dict" a
           dictionary of xml_list specify a label for the list xml_dict
           key for the XML element, the corresponding value for a list of
           corresponding element tag content
        '''
        xml_labels = Parsing_XML.parsing_label_list(labelname, xmlfile)[0].split(" ")
        xml_elements_dict = {}
        for per_label in xml_labels:
            per_xml_label_list = Parsing_XML.parsing_label_list(per_label, xmlfile)
            xml_elements_dict[per_label] = per_xml_label_list[0]
        return xml_elements_dict


class TestPerformance:

        # Private
        # Private comman
    def _getnumbits(self, rateless):
        """
        function: Converts "M-K" to bit
        """
        if rateless[-1] == "M":
            return int(float(rateless[:-1])) * 1024 * 1024
        elif rateless[-1] == "K":
            return int(float(rateless[:-1])) * 1024
        else:
            return int(float(rateless))
        
    def _server_iperf_exit(self, iperfpid, hostname="192.168.9.79",
                           username="root", password="baicells",port="22"):
        """
        funcition: kill server's process
        """
        port = int(port)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port, username, password)

        stdin,stdout,stderr=client.exec_command("kill -9 %s ;echo $? | tr -d '\n'" % iperfpid)
        returncode = stdout.read()
        logger.info(returncode)
        if int(returncode) > 0:
            logger.error("iperf process  %s exit faild " % iperfpid)
            return False
        else:
            logger.info("iperf process %s exit successful" % iperfpid)
            return True

    def _client_iperf_exit(self, pid):
        """
        function: kill client's process
        """
        try:
            os.system("taskkill /F /T /PID %s" % pid)
            print "%s pid exit sucessful" % pid
            return True
        except:
            print "%s pid exit have some error" % pid
            return False

    def _cilent_thread_exit(self, thread):
        """
        function: kill client's process
        """
        try:
            thread.kill()
            return True
        except:
            print "thread %s exit faild" % thread.pid()
            return False
        
        # Private Perfmance
        # Linux server functions
        # Linux server start iperf server	
    def _iperf_server_recive(self,listingmode="UDP", interval=10,listingport="27140",
                             hostname="192.168.9.79", username="root", password="baicells",
                             port="22"):
	'''
        server:linux
        function: uplink performance test (udp)
        type:iperf recive
	'''
        port = int(port)
	client=paramiko.SSHClient()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	client.connect(hostname, port, username, password)
	if listingmode == "UDP":
            cmd_start_server = "iperf -s -u -i %s -p %s & " % (interval,listingport)
        else:
            cmd_start_server = "iperf -s -i %s -p %s & " % (interval,listingport)
            # stdin,stdout,stderr=client.exec_command("killall -9 iperf") # kill iperf
            # time.sleep(3)
	stdin,stdout,stderr=client.exec_command(cmd_start_server)
	time.sleep(1)
	stdin,stdout,stderr = client.exec_command("ps aux | grep iperf | grep %s | head -n 1 | awk -F ' ' '{printf $2}' | tr -d '\n'" % listingport)
	iperfpid = stdout.read()
	client.close()
	if iperfpid:
            logger.info("iperf server start by pid %s" % iperfpid)
	    return iperfpid
	else:
            return None

        # Linux server start iperf client
    def _iperf_server_send(self,size="10240m",testtime=60, listingmode="UDP",
                           clientip="192.168.100.103",interval=10,
                           serverip="192.168.9.79",
                           listingport="27141", username="root", password="baicells", port=22):
        port = int(port)
	client=paramiko.SSHClient()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	client.connect(serverip, port, username, password)
	if listingmode is "UDP":
            cmd_send = "echo "" > iperf.log;iperf -u -c %s -b %s -l 1024 -t %s -i %s -p %s  > iperf.log" %\
                       (clientip, size, testtime, interval,listingport)
        else:
            cmd_send = "iperf -c %s -b %s -l 1024 -t %s -i %s -p %s" %(clientip, size, time, interval,listingport)
	stdin,stdout,stderr=client.exec_command(cmd_send)
	message = stdout.read()
	stdin,stdout,stderr=client.exec_command("cat iperf.log")
	result = stdout.read()
	logger.info(result)
	if listingmode == "UDP":
            try:
	        test = re.findall(r'Server Report:(.*?)bits/sec',result,re.S)
                result = re.findall(r'Bytes(.*?)$',test[0],re.S)
                resultbits = self._getnumbits(result[0].strip())
                return resultbits
            except:
                return None
        else:
            try:
                test = re.findall(r'sec(.*?)bits/sec',result,re.S)
                result = test[-1].split("  ")
                resultbits = self._getnumbits(result[-1].strip())
                return resultbits
            except:
                return None

        # windows functions
        # windows start iperf recive
    def _iperf_client_recive(self, iperfpath="E:\iperf2\iperf.exe",
                             listingmode="UDP", listingport="27141",interval=10):
        if listingmode == "UDP":
            cmd = "%s -s -u -i %s -p %s" %(iperfpath, interval,listingport)
        else:
            cmd = "%s -s -i %s -p %s" % (iperfpath, interval,listingport)
        p = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        status = []
        while True:
            while not self.Status.empty():
                status.append(self.Status.get())
                if "CLOSED" in status:
                    self._cilent_thread_exit(p)
                    return True
        
        # windows start iperf send
    def _iperf_client_send(self,size="10240m",testtime="60",
                           iperfpath="E:\iperf2\iperf.exe",
                           listingmode="UDP", interval=10,
                           serverip="192.168.9.79",listingport="27140"):
        """ client:windows
            function:performance
            type: iperf send test
        """
        if listingmode == "UDP":
            testcmd = "%s -u -c %s -b %s -l 1024 -t %s -i %s -p %s" % (iperfpath,serverip,size,testtime,interval,listingport)
        else:
            testcmd = "%s -c %s -b %s -l 1024 -t %s -i 10 -p %s" %(iperfpath,serverip, size, testtime,interval,listingport)
        p = subprocess.Popen(testcmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)  
	stdout, stderr = p.communicate()
	logger.info(stdout)
	if listingmode == "UDP":
            try:
	        test = re.findall(r'Server Report:(.*?)bits/sec',stdout,re.S)
                result = re.findall(r'Bytes(.*?)$',test[0],re.S)
                resultbits = self._getnumbits(result[0].strip())
                logger.info(resultbits)
                return resultbits
            except:
                return None
        else:
            try:
                test = re.findall(r'sec(.*?)bits/sec',stdout,re.S)
                result = test[-1].split("  ")
                resultbits = self._getnumbits(result[-1].strip())
                return resultbits
            except:
                return None
                
        # Private Stress
        # Linux server functions
        # Linux server start iperf server
    def _iperf_server_recive_stress(self,hostname,username,subtime,
                                    password,port,listingport):
            
        client=paramiko.SSHClient()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	client.connect(hostname, port, username, password)
	startserver = "echo "" > iperf.log;iperf -s -u -i %s -p %s > iperf.log & " % (subtime,listingport)
	stdin,stdout,stderr=client.exec_command(startserver)
	time.sleep(1)
	stdin,stdout,stderr = client.exec_command("ps aux | grep iperf | grep %s | head -n 1 | awk -F ' ' '{printf $2}' | tr -d '\n'" % listingport)
	iperfpid = stdout.read()
	client.close()
	if iperfpid:
            logger.info("iperf server start by pid %s" % iperfpid)
            self.Status.put(iperfpid)
	    return iperfpid
	else:
            return None

        # Linux server start iperf send
    def _iperf_server_send_stress(self,size="10240m",testtime=60, listingmode="UDP",
                                 clientip="192.168.100.103",interval=10,
                                 serverip="192.168.9.79",
                                 listingport="27144", username="root", password="baicells", port=22):
        port = int(port)
	client=paramiko.SSHClient()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	client.connect(serverip, port, username, password)
	if listingmode == "UDP":
            cmd_send = "iperf -u -c %s -b %s -l 1024 -t %s -i %s -p %s &" %(clientip, size, testtime, interval,listingport)
        else:
            cmd_send = "iperf -c %s -b %s -l 1024 -t %s -i %s -p %s &" %(clientip, size, testtime, interval,listingport)

        starttime = datetime.datetime.now()
	stdin,stdout,stderr=client.exec_command(cmd_send)
	client.close()
	return True

	# windows start iperf recive
    def _iperf_client_recive_stress(self, exportspeed, testtime, iperfpath="E:\iperf2\iperf.exe",
                                    listingmode="UDP", listingport="27145",interval=10):
        if listingmode == "UDP":
            cmd = "%s -s -u -i %s -p %s" %(iperfpath, interval,listingport)
        else:
            cmd = "%s -s -i %s -p %s" % (iperfpath, interval,listingport)
        p = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	logger.info("clien recive start by thread %s" % p.pid)
	clientstatus = []
	for i in range(7):
            line = p.stdout.readline()
            line = line.strip()
            logger.info(line)
        testtime = "%.1f" % float(testtime)
        self.checktime = 0
	while True:
            time.sleep(float(interval))
            line = p.stdout.readline()
            line = line.strip()
            logger.info(line)
            testspeed = re.findall(r'Bytes  (.*?)bits/sec',line,re.S)
            lossrate = re.findall(r'\((.*?)%\)',line,re.S)
            timelog = re.findall(r'\] (.*?)\ sec',line,re.S)
        # test speed check
            if len(testspeed) > 0:
                testrate = "".join(testspeed[0].split())
                testbits = self._getnumbits(testrate)
                if testbits < exportspeed:
                    self.status.put("LOWSPEED")
                    self._cilent_thread_exit(p)
                    return False
                # loss check  
            if listingmode == "UDP":
                if len(lossrate) > 0:
                    if float(lossrate[0]) > 0:
                        self.status.put("LOSS")
                        self._cilent_thread_exit(p)
                        return False
                # testtime check
            if len(timelog) > 0:
                timelist= timelog[0].split('-')
                self.checktime = 0
                if testtime in timelist:
                    logger.info("test finsh")
                    self._cilent_thread_exit(p)
                    return True
            else:
                self.checktime += 1
                if self.checktime >= 3:
                    logger.error("test break")
                    self.status.put("CLIENTCANCEL")
                    self._cilent_thread_exit(p)
                    return False

	# windows start iperf send udp
    def _iperf_client_send_stress_udp(self, path, serverip, subtime, size, times, port):
        """client:windows
            mode:tcp
            type:stress
        """
        testcmd = "%s -u -c %s -b %s -l 1024 -t %s -i %s -p %s" %(path,serverip, size, times, subtime, port)
        starttime = datetime.datetime.now()
        p = subprocess.Popen(testcmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.Status_client.put("CLIENTSTART")
        returncode = p.poll()
        serverstatus = []
        while returncode is None:
            line = p.stdout.readline()
            line = line.strip()
            logger.info(line)
            time.sleep(1)
            returncode = p.poll()
            while not self.Status_server.empty():
                serverstatus.append(self.Status_server.get())
            if "LOSS" in serverstatus:
                self._cilent_thread_exit(p)
                return False
            if "LOWSPEED" in serverstatus:
                self._cilent_thread_exit(p)
                return False
        if not returncode:
            endtime = datetime.datetime.now()
            testtime = (endtime - starttime).seconds
            if abs(int(testtime) - int(times)) > subtime:
                self.Status.put("CLIENTCANCEL")
                self.Status_client.put("CLIENTCANCEL")
                self._cilent_thread_exit(p)
                return False
	self.Status.put("CLIENTCLOSED")
	self.Status_client.put("CLIENTCANCEL")
	return True
	
        # windows start iperf send tcp
    def _iperf_client_send_stress_tcp(self, path, serverip, size, times, port, rateless,subtime):
        """client:windows
            mode:tcp
            type:stress
        """
        ratebits = self._getnumbits(rateless)
        testcmd = "%s -c %s -b %s -l 1024 -t %s -i %s -p %s" %(path,serverip, size, times, subtime, port)
        starttime = datetime.datetime.now()
        p = subprocess.Popen(testcmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        returncode = p.poll()
        result = []
        while returncode is None:
            time.sleep(1)
            line = p.stdout.readline()
            returncode = p.poll()
            line = line.strip()
            logger.info(line)
            test = re.findall(r'Bytes  (.*?)bits/sec',line,re.S)
            if len(test) > 0:
                test = "".join(test[0].split())
                logger.info(test)
                testbits = self._getnumbits(test)
                if testbits < ratebits:
                    return False
        if not returncode:
            endtime = datetime.datetime.now()
            testtime = (endtime - starttime).seconds
            if abs(int(testtime) - int(times)) >= subtime:
                logger.error( "test is break")
                return False
        stdout, stderr = p.communicate()
	logger.info(stdout)
	return True

	# linux iperf recive test status check
    def _iperf_server_check_status(self, hostname, username,subtime, password, port, expectrate):
        port = int(port)        
	client=paramiko.SSHClient()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	client.connect(hostname, port, username, password)
	clientstatus = []
	while True:
                time.sleep(int(subtime))
		while not self.Status_client.empty():
                    clientstatus.append(self.Status_client.get())
                if "CLIENTSTART" in clientstatus:
                    try:
                        stdin,stdout,stderr=client.exec_command("cat iperf.log | tail -n 1 | awk -F'(' '{print $2}' | sed -e s/\%\)//g | tr -d '\n'")
                        message = stdout.read()
                        if int(message) > 0:
                            self.Status.put("LOSS")
                            self.Status_server.put("LOSS")
                            client.close()
                            return False
                    except:
                        self.Status.put("LOSS")
                        self.Status_server.put("LOSS")
                        client.close()
                        return False
                    try:
                        stdin, stdout, stderr = client.exec_command("cat iperf.log | tail -n 1 | awk -F' ' '{print $7 $8}' | tr -d 'bits/sec\n'")
                        testbits = stdout.read()
                        testbits = self._getnumbits(testbits)
                        if testbits < expectrate:
                            self.Status.put("LOWSPEED")
                            self.Status_server.put("LOWSPEED")
                            client.close()
                            return False
                    except:
                        self.Status.put("LOWSPEED")
                        self.Status_server.put("LOWSPEED")   
                        client.close()
                        return False
		if "CLIENTCLOSED" or "CLIENTCANCEL" in clientstatus:
                    client.close()
                    break
        return True

        # Private FTP
        ## FTP Test
    def _Download_FTP(self,testtime=60, remotepath="lp02",localpath="F:/TMP/lp01",
                      host="192.168.9.79", username="ftpuser", password="888888"):
	'''
	FTP service.
	host: the conneced host IP address
	username: login host name
	password: login host password
	remotepath: storage path of download file
	localpath： local path of saved file
	'''
	testtime=int(testtime)
	ftp = FTP()
	try:
	    ftp.set_debuglevel(2)
	    ftp.connect(host, 21)
	    ftp.login(username, password)
	except:
            self.Status.put("LOGIN")
            return False
	try:
            ftp.set_pasv(True)
            ftp.dir()
        except:
            ftp.set_pasv(False)
	bufsize = 1024
	starttime = time.time()
	logger.info("start down load times is %s" %starttime)
	teststatus = []
	while True:
            timenow = time.time()
            if timenow - starttime > testtime:
                break  
	    fp = open(localpath, 'w')
	    try:  
		ftp.retrbinary('RETR ' + remotepath, fp.write, bufsize)
	    except:
                self.Status.put("ERROR")
                break
            while not self.Status.empty():
                teststatus.append(self.Status.get())
            if "LOW" in teststatus:
                self.Status.put("LOW")
                break
        fp.close()
	ftp.set_debuglevel(0)
	ftp.quit()
	return True

    def _Upload_FTP(self, testtime, remotepath,localpath,
                    host, username, password):
	'''
	FTP upload service.	
	host: the conneced host IP address	
	username: login host name
	password: login host password
	remotepath: storage path of download file
	localpath： local path of saved file
	'''
	ftp = FTP()
	try:
	    ftp.set_debuglevel(2)
	    ftp.connect(host, 21)
	    ftp.login(username, password)
	except:
            self.Status.put("LOGIN")
            return False
	    #ftp.pwd()
        """
        try:
            ftp.set_pasv(True)
            ftp.cwd("/home/ftpuser") 
        except:
            ftp.set_pasv(False)
            ftp.cwd("/home/ftpuser")
        """
	bufsize = 1024
	starttime = time.time()
	teststatus = []
	while True:
            timenow = time.time()
            if timenow - starttime > testtime:
                break
	    fp = open(localpath, 'r')
	    try:
	        ftp.storbinary('STOR ' + remotepath, fp, bufsize)
	    except:
                self.Status.put("ERROR")
                break 
            while not self.Status.empty():
                teststatus.append(self.Status.get())
            if "LOW" in teststatus:
                self.Status.put("LOW")
                break
	ftp.set_debuglevel(0)
	fp.close()
	ftp.quit()
	return True

        ### Test keywords
        ### iperf up test by single thread of performance
    def iperf_up_perf_single(self,sysargs,xmlargs):
        """
        Function: iperf up test by single thread of performance 
        Testserver (linux start iperf recive);
        client (windows start iperf send)
        """
        exportrate = self._getnumbits(sysargs["expectrate"])
        # Linux start iperf server recive
        pidnum = self._iperf_server_recive("UDP",xmlargs["interval"],
                                           27999,xmlargs["serverip"],
                                           "root",xmlargs["serverpw"], 22)
        # windows start iperf client send
        if pidnum:
            testrate = self._iperf_client_send(xmlargs["size"],
                                               int(sysargs["testtime"]),
                                               xmlargs["iperfpath"],
                                               "UDP",
                                               xmlargs["interval"],
                                               xmlargs["serverip"],
                                               27999)
            self._server_iperf_exit(pidnum)
        else:
            logger.error( "Testserver(linux) start iperf recive faild")
            return False
        if testrate:
            if os.path.exists(xmlargs["log"]):
                os.remove(xmlargs["log"])
            f = open(xmlargs["log"], 'a')
            f.write('UDP Peak bandwidth Test(iperf up)\n')
            f.write("%.2f" % float(testrate / 1024.00 / 1024.00))
            f.close()
            if testrate > exportrate:
                logger.info("Test is pass")
                return True
            else:
                logger.error("Actual rate below expected, test is faild")
                return False
        else:
            logger.error("Test result is None, please check it")
            return False                    

        # iperf down test single thread of performance        
    def iperf_down_perf_single(self,sysargs,xmlargs):
        exportrate = self._getnumbits(sysargs["expectrate"])
        # start client recive
        self.Status = Queue.Queue()
        client_recive = threading.Thread(target=self._iperf_client_recive,
                                         name="client",
                                         args=(xmlargs["iperfpath"],
                                               "UDP",
                                               27888,
                                               xmlargs["interval"]))
        client_recive.setDaemon(True)
        client_recive.start()
        logger.info("client start revice")
        time.sleep(3)
        try:
            testrate = self._iperf_server_send(xmlargs["size"],
                                               int(sysargs["testtime"]),
                                               "UDP",
                                               xmlargs["clientip"],
                                               xmlargs["interval"],
                                               xmlargs["serverip"],
                                               27888,
                                               "root",
                                               xmlargs["serverpw"],
                                               22)
            logger.info(" test rate is %s" % testrate)
            if os.path.exists(xmlargs["log"]):
                os.remove(xmlargs["log"])
            f = open(xmlargs["log"], 'a')
            f.write('UDP Peak bandwidth Test(iperf down)\n')
            f.write("%.2f" % float(testrate / 1024 / 1024))
            f.close()
            self.Status.put("CLOSED")
            if testrate > exportrate:             
                logger.info("Test is pass")
                return True
            else:
                logger.error( "Actual rate below expected, test is faild")
                return False
        except:
            logger.error("Test result is None, please check it")
            return False

        # udp stress upload test by iperf 
    def iperf_client_stress_udp(self,sysargs,xmlargs):
        """client:windows
            mode:udp
            type:stress
        """
        expectspeed = self._getnumbits(sysargs["expectrate"])
        self.Status =Queue.Queue()
        self.Status_server = Queue.Queue()
        self.Status_client = Queue.Queue()
        test = []
        server_recive = threading.Thread(target=self._iperf_server_recive_stress,
                                         name="thread1",
                                         args=(xmlargs["serverip"],
                                               "root",
                                               xmlargs["interval"],
                                               xmlargs["serverpw"],
                                               22,
                                               27222))
        client_sent = threading.Thread(target=self._iperf_client_send_stress_udp,
                                       name="thread2",
                                       args=(xmlargs["iperfpath"],
                                             xmlargs["serverip"],
                                             xmlargs["interval"],
                                             xmlargs["lsize"],
                                             int(sysargs["testtime"]),
                                             27222))
        server_check = threading.Thread(target=self._iperf_server_check_status,
                                        name="thread3",
                                        args=(xmlargs["serverip"],
                                              "root",
                                              xmlargs["interval"],
                                              xmlargs["serverpw"],
                                              22,
                                              expectspeed))
        client_sent.setDaemon(True)
        server_check.setDaemon(True)
        server_recive.start()
        server_recive.join()
        while not self.Status.empty():
            test.append(self.Status.get())
        pidnum = test[0]
        for item in test:
            if pidnum:
                client_sent.start()
                server_check.start()
                server_check.join()
                client_sent.join()
        self._server_iperf_exit(pidnum,
                                xmlargs["serverip"],
                                "root",
                                xmlargs["serverpw"],
                                22)
        while not self.Status.empty():
            test.append(self.Status.get())
        if "LOSS" in test:
            logger.error( "There is have loss in udp test")
            return False
        elif "LOWSPEED" in test:
            logger.error( "Speed is lower than expecet speed")
            return False
        elif "CLIENTCANCEL" in test:
            logger.error("Test is Interrupt")
            return False
        else:
            logger.info("Test is pass")
            return True           
	
        # tcp stress upload test by iperf
    def iperf_tcp_stress_up(self,sysargs,xmlargs):
            # start test server(linux) iperf_server recive
        pidnum = self._iperf_server_recive("TCP",
                                           xmlargs["interval"],
                                           27999,
                                           xmlargs["serverip"],
                                           "root",
                                           xmlargs["serverpw"],
                                           22)
        logger.info(" server recive start by pid %s" %pidnum)
        if pidnum:
            returncode = self._iperf_client_send_stress_tcp(
                         xmlargs["iperfpath"],
                         xmlargs["serverip"],
                         xmlargs["lsize"],
                         int(sysargs["testtime"]),
                         27999,
                         sysargs["expectrate"],
                         xmlargs["interval"])
            self._server_iperf_exit(pidnum,
                                    xmlargs["serverip"],
                                    "root",
                                    xmlargs["serverpw"],
                                    22)
        else:
            logger.info("test server(linux) start iperf_server faild")
            return False    
        if returncode:
            logger.info("tcp upload stress test is pass")
            return True
        else:
            logger.error("tcp upload stress test is faild")
            return False

        # stress download test by iperf
    def iperf_stress_down(self,sysargs,xmlargs,listingmode):
        # start test machine(windows) iperf_server recive
        """
        self._iperf_client_recive(self, iperfpath="E:\iperf2\iperf.exe",
                                  listingmode="UDP", listingport="27141",interval=10):
        """
        statuslist=[]
        expectspeed = self._getnumbits(sysargs["expectrate"])
        self.pid_server=Queue.Queue()
        self.status = Queue.Queue()
        self.iperf_server =Queue.Queue()
        self.iperf_client = Queue.Queue()
        thread_recive = threading.Thread(target=self._iperf_client_recive_stress,
                                         name="thread1",
                                         args=(expectspeed,
                                               int(sysargs["testtime"]),
                                               xmlargs["iperfpath"],
                                               listingmode,
                                               27111,
                                               xmlargs["interval"]))
        thread_send = threading.Thread(target=self._iperf_server_send_stress,
                                       name="thread2",
                                       args=(xmlargs["lsize"],
                                             int(sysargs["testtime"]),
                                             listingmode,
                                             xmlargs["clientip"],
                                             xmlargs["interval"],
                                             xmlargs["serverip"],
                                             27111,
                                             "root",
                                             xmlargs["serverpw"],
                                             22))
        thread_recive.setDaemon(True)
        thread_send.setDaemon(True)
        thread_recive.start()
        time.sleep(3)
        thread_send.start()
        thread_send.join()
        thread_recive.join()
        while not self.status.empty():
            statuslist.append(self.status.get())
        if "LOSS" in statuslist:
            logger.error("There is have loss in test")
            return False
        elif "LOWSPEED" in statuslist:
            logger.error("Speed is lower than expecet speed")
            return False
        elif "CLIENTCANCEL" in statuslist:
            logger.error("Test is Interrupt")
            return False
        else:
            return True  
        
        # iperf muilt 
    def _iperf_client_send_mulit(self, path, serverip,testmode, size, time, port):
        """ client:windows
            function:performance
            type: iperf send test
        """
            
        print testmode
        if testmode == "UDP":
            testcmd = "%s -u -c %s -b %s -l 1024 -t %s -i 60 -p %s" % (path,serverip,size,time,port)
        else:
            testcmd = "%s -c %s -b %s -l 1024 -t %s -i 60 -p %s" %(path,serverip, size, time, port)
        p = subprocess.Popen(testcmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)  
	stdout, stderr = p.communicate()
	logger.info(stdout)
	if testmode == "UDP":
	    test = re.findall(r'Server Report:(.*?)bits/sec',stdout,re.S)
            result = re.findall(r'GBytes(.*?)$',test[0],re.S)
            self.Result.put("client:%s"%(result[0].strip() + "bits/sec"))
            return "client to server UDP :%s" % (result[0].strip() + "bits/sec")
        else:
            test = re.findall(r'sec(.*?)bits/sec',stdout,re.S)
            result = test[-1].split("  ")
            self.Result.put("client:%s" % (result[-1].strip() + "bits/sec"))
            return "client to server TCP: %s" % (result[-1].strip() + "bits/sec")

    def _iperf_server_send_mulit(self, hostname, username, password, port, serverip, testmode, size, time, listingport):
        port = int(port)
	self.hostname = hostname
	self.username = username
	self.password = password
	self.port = port

	client=paramiko.SSHClient()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	client.connect(hostname = self.hostname, port=self.port, username = self.username, password = self.password)
	if testmode == "UDP":
            cmd_send = "iperf -u -c %s -b %s -l 1024 -t %s -i 60 -p %s > iperf.log" %(serverip, size, time, listingport)
        else:
            cmd_send = "iperf -c %s -b %s -l 1024 -t %s -i 60 -p %s" %(serverip, size, time, listingport)
	stdin,stdout,stderr=client.exec_command(cmd_send)
	message = stdout.read()
	stdin,stdout,stderr=client.exec_command("cat iperf.log")
	result = stdout.read()
	print result
	if testmode == "UDP":
	    test = re.findall(r'Server Report:(.*?)bits/sec',result,re.S)
            result = re.findall(r'GBytes(.*?)$',test[0],re.S)
            self.Result.put("server:%s" %(result[0].strip() + "bits/sec"))
            return "server to client UDP: %s" %(result[0].strip() + "bits/sec")
        else:
            test = re.findall(r'sec(.*?)bits/sec',result,re.S)
            result = test[-1].split("  ")
            self.Result.put("server:%s"%(result[-1].strip() + "bits/sec"))
            return "server to client TCP: %s" %(result[-1].strip() + "bits/sec")     

    def iperf_mulit_test(self,server_ip,server_loginname, server_password,
                       server_port, server_listingport,client_path,client_ip,
                       client_listingport,testmode, testsize, testtime):
        self.Result =Queue.Queue()
        result = []
        t1 = threading.Thread(target=self._iperf_client_send_mulit, name="thread1", args=(client_path,
                                                                                    server_ip,testmode,
                                                                                    testsize, testtime,
                                                                                    server_listingport,))
        t2 = threading.Thread(target=self._iperf_server_send_mulit, name="thread2", args=(server_ip,
                                                                                    server_loginname, server_password,
                                                                                    server_port, client_ip, testmode,
                                                                                    testsize, testtime,
                                                                                    client_listingport,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        while not self.Result.empty():
            result.append(self.Result.get())
        allresult = {}
        for item in result:
            if "server" in item :
                allresult["server"] = item.split(":")[1]
                print "server result is %s" % item.split(":")[1]
            else:
                allresult["client"] = item.split(":")[1]
                print "client result is %s" % item.split(":")[1]
        return allresult

        ## FTP Test
    def Ftp_Perftest(self,sysargs,xmlargs):
        expectspeed = self._getnumbits(sysargs["expectrate"])
        self.Status =Queue.Queue()
        test = []
        testtime = int(sysargs['testtime'])
        if sysargs["upload"] is "DOWN":
            ftptest = threading.Thread(target=self._Download_FTP, name="downloadftp",  
                                        args=(testtime,
                                              xmlargs["downfile"],
                                              xmlargs["downpath"],
                                              xmlargs["fhost"],
                                              xmlargs["ftpuser"],
                                              xmlargs["ftppw"]))
        else:
            ftptest = threading.Thread(target=self._Upload_FTP,
                                       name = "uploadftp",
                                       args=(testtime,
                                             xmlargs["ulfile"],
                                             xmlargs["uppath"],
                                             xmlargs["fhost"],
                                             xmlargs["ftpuser"],
                                             xmlargs["ftppw"]))
        ftprate = threading.Thread(target=self.syslog_save_rate, name="getrate",
                                   args=(testtime,
                                         xmlargs["chost"],
                                         xmlargs["log"],
                                         "root",
                                         "root123",
                                         "27149"))
        ftptest.setDaemon(True)
        ftprate.setDaemon(True)
        logger.info("Ftp test is start")
        ftptest.start()
        ftprate.start()
        ftptest.join()
        ftprate.join()
        return 

        # Save syslog rate 
    def syslog_save_rate(self,testtime,hostname,logfile,username, password, port):
        port = int(port)
        testtime = int(testtime)
        #ratetime = int(ratetime)
        GET_DL = re.compile(r'dlTtlTpt=(.*?)bps')
        GET_UL = re.compile(r'ulTtlTpt=(.*?)bps')
        if os.path.exists(logfile):
            os.remove(logfile)
        client=paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port, username, password)
        ssh = client.invoke_shell()
        time.sleep(1)
        cmd = "tail -f /tmp/log/syslog | grep  dlTtlTpt"
        ssh.send(cmd)
        ssh.send('\n')
        buff = ''        
        starttime = time.time()
        f = open(logfile, 'a')
        f.write('TCP Peak bandwidth Test(FTP)\n')
        f.write('Time, DL_Rate, UL_Rate\n')
        f.close()
        while time.time() - starttime < testtime:
            resp = ssh.recv(512)
            dlrate = GET_DL.findall(resp)
            ulrate = GET_UL.findall(resp)
            if len(dlrate) > 0:
                logger.info("%s, %s" % (dlrate[0][:-1],ulrate[0][:-1]))
                f = open(logfile, 'a')
                f.write('%s, %s, %s\n' % (time.strftime('%Y:%m:%d:%H:%M:%S',time.localtime(time.time())),dlrate[0][:-1],ulrate[0][:-1]))
                f.close()
        client.close
        return True

        # check syslog rate
    def _syslog_check_rate(self,testtime=30,expectd="10M",hostname="192.168.107.216",username="root", password="root123", port="27149"):
        port = int(port)
        testtime = int(testtime)
            #ratetime = int(ratetime)
        GET_LENGTH = re.compile(r'= (\d+)')
        if os.path.exists(logfile):
            os.remove(logfile)
        client=paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port, username, password)
        ssh = client.invoke_shell()
        time.sleep(1)
        cmd = "tail -f /tmp/log/syslog | grep TTI"
        ssh.send(cmd)
        ssh.send('\n')
        buff = ''        
        starttime = time.time()
        f = open(logfile, 'a')
        while time.time() - starttime < testtime:
            resp = ssh.recv(512)
            rate = GET_LENGTH.findall(resp)
            if len(rate) > 0:
                if rate[0] < expectd:
                    print "Test Rate is lower than expect"
                    return False
        client.close
        return True


def recive_args():
    parser = OptionParser()
    parser.add_option("-m", "--mode", dest="testmode",
                      help="Test mode TCP/UDP.\
                            default=TCP")
    parser.add_option("-u", "--ul", dest="upload",
                     help="D or U\
                            default=D.")
    parser.add_option("-t", "--time", dest="testtime",
                      help="Test seconds.\
                            default:600.")
    parser.add_option("-e", "--MB", dest="expectrate",
                     help="Expectd rate of total.\
                           default: 1M.")
    parser.add_option("-b","--bandwidth", dest="bandwidth",
                      help="Bandwidth:10MHz/20MHz.\
                           default: 10MHz.")
    parser.add_option("-s","--sa", dest="subframe",
                      help="SubFrame Assignment:1/2.\
                           default: 2.")
    parser.add_option("-p","--ssp", dest="sspframe",
                      help="Special SubFrame Patterns:5/7.\
                           default: 7.")
    parser.add_option("-l","--little",dest="little",
                      help="Little pacage test:Y/N\
                          default:N")
    (options, args) = parser.parse_args()
    test_args = {}
    if options.testmode is None:
        options.download = "TCP"
    if options.upload is None:
        options.upload = "D"
    if options.testtime is None:
        options.testtime = "60"
    if options.expectrate is None:
        options.expectrate = "1M"
    if options.bandwidth is None:
        options.bandwidth = "10MHz"
    if options.subframe is None:
        options.subframe = "2"
    if options.sspframe is None:
        options.sspframe = "7"
    if options.little is None:
        options.little = "N"
    test_args["mode"] = options.testmode
    test_args["upload"] = options.upload
    test_args["testtime"] = options.testtime
    test_args["expectrate"] = options.expectrate
    test_args["bandwidth"] = options.bandwidth
    test_args["subframe"] = options.subframe
    test_args["sspframe"] = options.sspframe
    test_args["little"] = options.little
    return test_args

def setloger():
    logger = logging.getLogger('test')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('testlog.txt')
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(asctime)s - %(name)s -%(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)

def do_clicmd(hostname, username, password, port, command):
    '''
    Set the basic configuration in cli.txt.	
    hostname: the conneced host IP address		
    username: login host name		
    password: login host password	
    path: storage path of the configuration script and log
    '''
    port = int(port)	
    client=paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port, username, password)	
    stdin,stdout,stderr=client.exec_command("%s" % command)
    returncode=stdout.read()
    client.close()
    return returncode

BANDWIDTHLIST = {
    "10MHz": "n50",
    "20MHz": "n100"}

SETBANFCMD = "cli -c 'oam.set LTE_DL_BANDWIDTH %s'"
SETSACMD = "cli -c 'oam.set LTE_TDD_SUBFRAME_ASSIGNMENT %s'"
SETSPCMD = "cli -c 'oam.set LTE_TDD_SPECIAL_SUB_FRAME_PATTERNS %s'"
GETBANDCMD = "cli -c 'oam.getwild LTE_DL_BANDWIDTH' | awk -F ' ' '{print $2}' | tr -d '\n'"
GETSACMD = "cli -c 'oam.getwild LTE_TDD_SUBFRAME_ASSIGNMENT' | awk -F' ' '{print $2}' | tr -d '\n'"
GETSPCMD = "cli -c 'oam.getwild LTE_TDD_SPECIAL_SUB_FRAME_PATTERNS' | awk -F' ' '{print $2}' | tr -d '\n'"

def setting(inputargs, ftpargs):
    # bandwidth seting
    bandnow = do_clicmd(str(ftpargs["chost"]),"root",str(ftpargs["csshpw"]),
                       ftpargs["cport"],GETLGWCMD)
    if bandnow is BANDWIDTHLIST[inputargs["bandwidth"]] :
        logger.info("Bandwidth  is %s already" % inputargs["bandwidth"])
    else:
        bandcmd = SETLGWCMD % BANDWIDTHLIST[inputargs["bandwidth"]]
        returncode = do_clicmd(str(ftpargs["chost"]),"root",str(ftpargs["csshpw"]),
                               ftpargs["cport"],bandcmd)
        print returncode
        if returncode is "":
            logger.info("bandwidth mode is setting %s now" % inputargs["widthmode"]) 
        else:
            logger.error("bandwidth is setting fail")
            exit(1)
    # sa setting
    sanow = do_clicmd(str(ftpargs["chost"]),"root",str(ftpargs["csshpw"]),
                       ftpargs["cport"],GETSACMD)
    if sanow is inputargs["subframe"]:
        logger.info("SA is %s already" % inputargs["subframe"])
    else:
        sacmd = SETSACMD % inputargs["subframe"]
        returncode = do_clicmd(str(ftpargs["chost"]),"root",str(ftpargs["csshpw"]),
                               ftpargs["cport"],sacmd)
        if returncode is "":
            logger.info("SA is setting %s now" % inputargs["subframe"])
        else:
            logger.error("SA is setting fail")
            exit(1)
    # sp setting
    spnow = do_clicmd(str(ftpargs["chost"]),"root",str(ftpargs["csshpw"]),
                       ftpargs["cport"],GETSPCMD)
    if spnow is inputargs["sspframe"]:
        logger.info("SP is %s already" % inputargs["sspframe"])
    else:
        spcmd = SETSPCMD % inputargs["sspframe"]
        returncode = do_clicmd(str(ftpargs["chost"]),"root",str(ftpargs["csshpw"]),
                               ftpargs["cport"],spcmd)
        if returncode is "":
            logger.info("SP is setting %s now" % inputargs["sspframe"])
        else:
            logger.error("SP is setting fail")
            exit(1)
    return

def settestroute():
    """setup before test"""
    pass

    
if __name__ == "__main__":
    if os.path.exists("testlog.txt"):
        os.remove("testlog.txt")
    setloger()
    logger = logging.getLogger('test')
    sysargs = recive_args()
    logger.info("Input args is %s " %sysargs)
    xmlargs = Parsing_XML.specific_elements('comonlabel', 'args.xml')
    logger.info("Xml args is %s " % xmlargs)
    # Do cell setting
    # setting(inputargs, ftpargs)
    # Do ftp test setting
    
    #testjob = FtpStress()
    #testjob.Ftp_Stresstest(inputargs, ftpargs, ueargs)
    testobj = TestPerformance()
    if sysargs["little"] is "N":
        if sysargs['mode'] is "TCP":
            testobj.Ftp_Perftest(sysargs,xmlargs)
        else:
            if sysargs['upload'] is "U":
                testobj.iperf_up_perf_single(sysargs,xmlargs)
            else:
                testobj.iperf_down_perf_single(sysargs,xmlargs)
    else:
        if sysargs['mode'] == "TCP":
            if sysargs['upload'] is "U":
                testobj.iperf_tcp_stress_up(sysargs,xmlargs)
            else:
                testobj.iperf_stress_down(sysargs, xmlargs, "TCP")
        else:
            if sysargs['upload'] is "U":
                testobj.iperf_client_stress_udp(sysargs,xmlargs)
            else:
                testobj.iperf_stress_down(sysargs, xmlargs, "UDP")
