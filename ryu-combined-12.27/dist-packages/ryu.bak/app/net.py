__author__ = 'Johnny'

import time
import copy
import json

DOMAINID = 'domainId'
TYPE = 'type'
PATHTYPE = 'pathType'
TASK_ID = 'taskId'
SRC_IP = 'srcIp'
DST_IP = 'dstIp'
SRC_MAC = 'srcMac'
DST_MAC = 'dstMac'
SRC_SWITCH = 'srcSwitch'
DST_SWITCH = 'dstSwitch'
BANDWIDTH = 'bandwidth'
PARTPATH = 'path'
LABELS = 'labels'
NEXT_MAC = 'next_mac'
LOCAL_MAC = 'local_mac'
LAST_OUTPORT_NUM = 'last_outport_num'


TASK_DICT = {}  ##  taskid  < --- >  task objcet
REQ_LIST = []
#
# def getReq(req):
#     assert req in REQ_LIST  ##
#     return req    ##
# def assertReqInList(req):
#     return req in REQ_LIST   ##

def getTask(taskId):
    assert taskId in TASK_DICT.keys()

    return TASK_DICT[taskId]

def assertTaskInDict(taskId):
    return taskId in TASK_DICT.keys()

def delTask(taskId):
    assert taskId in TASK_DICT.keys()
    del TASK_DICT[taskId]

def registerTask(task):
    assert isinstance(task, Task)
    assert task.taskId not in TASK_DICT
    TASK_DICT[task.taskId] = task

def getMainPathEffect(edge):
    taskList = []
    for i in TASK_DICT:
        taskInstance = getTask(i)
        if taskInstance.checkEdgeInMainPath(edge):
            taskList.append(i)
    return taskList

def getBackupPathEffect(edge):
    taskList = []
    for i in TASK_DICT:
        taskInstance = getTask(i)
        if taskInstance.checkEdgeInBackupPath(edge):
            taskList.append(i)
    return taskList

class Task(object):

    def __init__(self, taskid, name=None, srcSwitch=None, dstSwitch=None, srcIp=None,
                 dstIp=None, srcMac=None, dstMac=None, *args, **kwargs):

        self.taskId = taskid

        if name:
            self.name = name
        else:
            self.name = 'Task ' + time.ctime(time.time())#time string

        self.srcSwitch = srcSwitch
        self.dstSwitch = dstSwitch

        self.srcIp = srcIp
        self.dstIp = dstIp

        self.srcMac = srcMac
        self.dstMac = dstMac
        self.next_mac = None
        self.local_mac = None
        self.bandwidth = {}
        self.last_outport_num = None
####################################################################################
        self.virPathSect = {}
        self.completPathVir = []
######################################################################################
        self.completPathMain = []
        self.crossDomainMain =[]
        self.mainPathSect = {}
        self.mainMpls = {}
        self.mainUnconfirmedDomain = []

        self.completPathBackup = []
        self.crossDomainBackup = []
        self.backupPathSect = {}
        self.backupMpls = {}
        self.backupUnconfirmedDomain = []

        self.deleteDomains = []

        self.status = False

        self.creatTime = time.time()


    def isEstablished(self):

        return self.status

    def getName(self):

        return self.name

    def getTaskId(self):
        return self.taskId

    def setSrcSwitch(self, srcSwitch):
        self.srcSwitch = srcSwitch

    def getSrcSwtich(self):
        return self.srcSwitch

    def setDstSwtich(self, dstSwtich):
        self.dstSwitch = dstSwtich

    def getDstSwitch(self):
        return self.dstSwitch

    def setSrcIp(self, srcIp):
        self.srcIp = srcIp

    def getSrcIp(self):
        return self.srcIp

    def setDstIp(self, dstIp):
        self.dstIp = dstIp

    def getDstIp(self):
        return self.dstIp

    def setBandwidth(self, bandwidth):
        self.bandwidth = bandwidth

    def getBandwidth(self):
        return self.bandwidth

    def setDeleteDomains(self, deleteList):
        self.deleteDomains = deleteList

    def getDeleteDomains(self):
        return self.deleteDomains

    def removeDeleteDomain(self, domainID):
        self.deleteDomains.remove(domainID)

    def isCheckToDelete(self):
        if not self.deleteDomains:
            return True
        return  False

    def taskSetIpFields(self, srcSwitch=None, dstSwitch=None, srcIp=None, dstIp=None, local_mac=None,
                      next_mac=None, last_outport_num=None, bandwidth=None):
        self.srcSwitch = srcSwitch
        self.dstSwitch = dstSwitch
        self.srcIp = srcIp
        self.dstIp = dstIp
        self.bandwidth = bandwidth
        self.local_mac = local_mac
        self.next_mac = next_mac
        self.last_outport_num = last_outport_num

    def taskSetMacFields(self, srcSwitch=None, dstSwitch=None, srcMac=None, dstMac=None,
                       last_outport_num=None, bandwidth=None):
        self.srcSwitch = srcSwitch
        self.dstSwitch = dstSwitch
        self.srcMac = srcMac
        self.dstMac = dstMac
        self.bandwidth = bandwidth
        self.last_outport_num = last_outport_num


#############################################################################################
    def getVirEdges(self):

        length = len(self.completPathVir)
        assert length % 2 == 0

        edges = []
        for i in range(length - 1):
            srcEndpoint = self.completPathVir[i]
            dstEndpoint = self.completPathVir[i + 1]

            edge = (srcEndpoint, dstEndpoint)
            edges.append(edge)

        return edges

    def setVirCompletePath(self, pathList):
        self.completPathVir = pathList

    def getVirSectorialPath(self, nodeTodomain,virEdges):

        self.virPathSect.clear()
        for in_port, out_port in virEdges:
            nodeDomain = nodeTodomain[in_port]
            assert nodeDomain == nodeTodomain[out_port]
            partPath = self.virPathSect.setdefault(nodeDomain, {})
            partPathList = partPath.setdefault('list', [])
            assert in_port not in partPathList
            partPathList.append(in_port)
            assert out_port not in partPathList
            partPathList.append(out_port)
        domainList = self.virPathSect.keys()
        self._set_main_cross_domain(domainList)

        length = len(self.completPathVir)
        for i in self.virPathSect:
            partPath = self.virPathSect[i]
            first = partPath['list'][0]
            last = partPath['list'][-1]
            firstIndex = self.completPathVir.index(first)
            if firstIndex == 0:#######domain1
                partPath['pre'] = 0
            else:############domain2
                partPath['pre'] = self.completPathVir[firstIndex - 1]
            lastIndex = self.completPathVir.index(last)
            if lastIndex == length - 1:
                partPath['post'] = 0
            else:
                partPath['post'] = self.completPathVir[lastIndex + 1]

        return self.virPathSect


###############################################################################################

    #divide a path into different paths
    def getMainEdges(self):

        length = len(self.completPathMain)
        edges = []
        for i in range(length - 1):
            srcEndpoint = self.completPathMain[i]
            dstEndpoint = self.completPathMain[i + 1]
            edge = (srcEndpoint, dstEndpoint)
            edges.append(edge)


        return edges


    def getBackupEdges(self):
        length = len(self.completPathBackup)
        edges = []

        for i in range(length - 1):
            srcEndpoint = self.completPathBackup[i]
            dstEndpoint = self.completPathBackup[i + 1]
            edge = (srcEndpoint, dstEndpoint)
            edges.append(edge)


        return edges

    def setCreatTime(self, time):

        self.creatTime = time


    def getTaskInfo(self):

        return "Task info"

    def setMainCompletePath(self, pathList):
        self.completPathMain = pathList#pathlist is a list

    def getMainCompletePath(self):
        return self.completPathMain

    def setBackupCompletePath(self, pathList):
        self.completPathBackup = pathList

    def getBackupCompletePath(self):
        return self.completPathBackup

    def getMainSectorialPath(self, nodeTodomain):#nodeTodomain is a node dict which include nodes in the domain
                                                    #dpid:domainID

        length = len(self.completPathMain)#completpathmain is a dpid list

        self.mainPathSect.clear()#############

        for node in self.completPathMain:
            assert node in nodeTodomain
            DomainID = nodeTodomain[node]
            partPath = self.mainPathSect.setdefault(DomainID, {})
            partPathList = partPath.setdefault('list', [])
            #assert node not in partPathList
            #partPathList.append(node)
            partPathList.append(node)

        #print self.mainPathSect
        #{1: {'list': [9120431834591789832L, 514, 517]}, 2: {'list': [773, 770, 2770919309952811793L]}}
        #partPath = {'list':[dpid.....]}
        #partPathList = [dpid......]

        for i in self.mainPathSect:
            partPath = self.mainPathSect[i]
            first = partPath['list'][0]
            last = partPath['list'][-1]
            firstIndex = self.completPathMain.index(first)
            if firstIndex == 0:#######domain1
                partPath['pre'] = 0
            else:############domain2
                partPath['pre'] = self.completPathMain[firstIndex - 1]
            lastIndex = self.completPathMain.index(last)
            if lastIndex == length - 1:
                partPath['post'] = 0
            else:
                partPath['post'] = self.completPathMain[lastIndex + 1]


        #print partPath
        #{'pre': 517, 'post': 0, 'list': [774, 771, 2770919309952811793L]}
        #should be two paths

        domainList = self.mainPathSect.keys()

        self._set_main_cross_domain(domainList)

        return self.mainPathSect

    def _set_main_cross_domain(self, domainList):#domains to cross
        self.crossDomainMain = domainList

    def getBackupSectorialPath(self, nodeTodomain):

        length = len(self.completPathBackup)
        self.backupPathSect.clear()
        for node in self.completPathBackup:
            assert node in nodeTodomain
            nodeDomain = nodeTodomain[node]
            partPath = self.backupPathSect.setdefault(nodeDomain, {})
            partPathList = partPath.setdefault('list', [])
            assert node not in partPathList
            partPathList.append(node)

        for i in self.backupPathSect:
            partPath = self.backupPathSect[i]
            first = partPath['list'][0]
            last = partPath['list'][-1]
            firstIndex = self.completPathBackup.index(first)
            if firstIndex == 0:
                partPath['pre'] = 0
            else:
                partPath['pre'] = self.completPathBackup[firstIndex - 1]
            lastIndex = self.completPathBackup.index(last)
            if lastIndex == length - 1:
                partPath['post'] = 0
            else:
                partPath['post'] = self.completPathBackup[lastIndex + 1]

        domainList = self.backupPathSect.keys()

        self._set_backup_cross_domain(domainList)

        return self.backupPathSect

    def _set_backup_cross_domain(self, domainList):
        self.crossDomainBackup = domainList

    def assignMainPathMpls(self, labelsList):
        tempList = copy.deepcopy(labelsList)
        self.mainMpls.clear()
        for i in self.mainPathSect:
            partPath = self.mainPathSect[i]
            labels = self.mainMpls.setdefault(i, [])
            length = len(partPath['list'])
            for i in range(length - 1):
                label = tempList[0]
                labels.append(label)
                tempList.remove(label)

        return labelsList

    def assignBackuPathMpls(self, labelsList):
        self.backupMpls.clear()
        tempList = copy.deepcopy(labelsList)

        for i in self.backupPathSect:
            partPath = self.backupPathSect[i]
            labels = self.backupMpls.setdefault(i, [])
            length = len(partPath['list'])
            for i in range(length - 1):
                label = tempList[0]
                labels.append(label)
                tempList.remove(label)

        return labelsList

    def makeDomainTaskAssign(self, domainId, type='main'):
        to_send = {}
        to_send[DOMAINID] = domainId
        to_send[TYPE] = 'taskAssign'
        to_send[PATHTYPE] = type
        to_send[TASK_ID] = self.taskId
        to_send[SRC_IP] = self.srcIp
        to_send[DST_IP] = self.dstIp
        to_send[SRC_MAC] = self.srcMac
        to_send[DST_MAC] = self.dstMac
        to_send[SRC_SWITCH] = self.srcSwitch
        to_send[DST_SWITCH] = self.dstSwitch
        to_send[BANDWIDTH] = self.bandwidth###
        to_send[NEXT_MAC] = self.next_mac   ##
        to_send[LOCAL_MAC] = self.local_mac   ##
        to_send[LAST_OUTPORT_NUM] = self.last_outport_num  ##

        for i in to_send.keys():
            if to_send[i] is None:
                to_send.pop(i)

        if type == 'main':
            to_send[PARTPATH] = self.virPathSect.get(domainId)#return a dict
            #to_send[LABELS] = self.mainMpls.get(domainId)
        elif type == 'backup':
            to_send[PARTPATH] = self.backupPathSect.get(domainId)
            to_send[LABELS] = self.backupMpls.get(domainId)

        sendMessage = json.dumps(to_send)
        return sendMessage

    def makeTaskDeleteMsg(self, domainId):
        to_send = {}
        to_send[TYPE] = 'taskDelete'
        to_send[DOMAINID] = domainId
        to_send[TASK_ID] = self.taskId

        send_message = json.dumps(to_send)
        return send_message

    def addMainUnconfirmDomain(self, dominaId):
        self.mainUnconfirmedDomain.append(dominaId)

    def addBackupUnconfirmDomain(self, domainId):
        self.backupUnconfirmedDomain.append(domainId)

    def removeMainUnconfirmDomain(self, domainId):
        assert domainId in self.mainUnconfirmedDomain
        self.mainUnconfirmedDomain.remove(domainId)

    def removeBackupUnconfirmDomain(self, domainId):
        assert domainId in self.backupUnconfirmedDomain
        self.backupUnconfirmedDomain.remove(domainId)

    def changeToEstablished(self):
        self.status = True

    def checkTaskStatus(self):
        if not self.mainUnconfirmedDomain and self.backupUnconfirmedDomain:
            if not self.isEstablished():
                self.changeToEstablished()
                return True
        return False

    def checkEdgeInMainPath(self, edge):
        edges = self.getMainEdges()
        if edge in edges:
            return True
        else:
            return False

    def checkEdgeInBackupPath(self, edge):
        edges = self.getBackupEdges()
        if edge in edges:
            return True
        else:
            return False

    def getBackupCrossDomains(self):
        return self.crossDomainBackup

    def getMainCrossDomains(self):
        return self.crossDomainMain

    def changeBackupToMain(self):
        self.completPathMain = self.completPathBackup
        self.crossDomainMain = self.crossDomainBackup
        self.mainPathSect = self.backupPathSect
        self.mainMpls = self.backupMpls

        self._set_backup_None()

    def _set_backup_None(self):
        self.backupMpls = {}
        self.completPathBackup = []
        self.backupPathSect = {}
        self.crossDomainMain = []


    def getAllDomains(self):
        newList = self.crossDomainMain
        for i in self.crossDomainBackup:
            if i not in newList:
                newList.append(i)

        return newList

    def getAllMpls(self):
        labels = self.mainMpls
        for i in self.backupMpls:
            if i not in labels:
                labels.append(i)

        return labels




