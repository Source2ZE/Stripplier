##################################################################
# Stripplier a.k.a. Stipper Applier
# Public script to implement source engine stripper .cfg into .vmf
# Made for Source 2 Zombie Escape (S2ZE) Project
# https://github.com/Source2ZE/Stripplier
# 
# Current version: 2.0.2 (1st January 2025)
# Created by: lameskydiver / chinny (lameskydiver on discord)
# 
# LICENSE: MIT License
# But feel free to give credits if you want!
##################################################################

#################
#    IMPORTS    #
#################

import re#regex
import os#directory

######################
#    DECLARATIONS    #
######################

#overall vmf structure
version = []
vis = []
view = []
palette = []
cc = []
light = []
bg = []
world = []
ents = []
cameras = []
cordons = []

#create dict for keyvalues that are/should be used extensively in stripper
#these are for references and should not be edited
#order from most unique to least unique
#thanks to moltard for the suggestion
ref = {
    'model':{},
    'id':{},
    'origin':{},
    'targetname':{},
    'classname':{},
    'hash':{}
}

#list of stripper blocks in dict formatting
stripper = []

################
#    ERRORS    #
################

#keeps record of lines to be used in error log per stripper block
#this is flushed if a block is processed successfully
error_block = []

#count of errors so far
error_count = 1

#dict of default error messages
error_dict = {
    'read':'The script has failed reading the input .vmf. This may indicate:\n\t* No .vmf was provided, or .vmf has different name and/or letter cases from what you have inputted.\n\t* .vmf is corrupt.\n\t* The script may not support your Source Engine game.\nIt is recommended that you attempt to fix the input .vmf first\nand notify the issue if you are confident that the .vmf is normal and functional.',
    'bsp':'The script has failed reading the input .bsp. This may indicate:\n\t* No .bsp was provided, or .bsp has different name and/or letter cases from what you have inputted.\n\t* .bsp is corrupt.\n\t* The script may not support your Source Engine game.\nIt is recommended that you try to recompile/recollect the .bsp first\nand notify the issue if you are confident that the .bsp is normal and functional.',
    'cfg':'The script has failed reading the input .cfg stripper. This may indicate:\n\t* No .cfg was provided, or .cfg has different name and/or letter cases from what you have inputted.\n\t* .cfg contains syntax errors.\nIt is very likely this error is due to a syntax error in the stripper.\nDouble check syntax for these symbols [ : , "  { } ] are correct!',
    'stripper':'The script has failed reading a specific block in the stripper. This may indicate:\n\t* Incorrect or invalid keyvalues were provided in the stripper.\n\t* Incorrect syntaxes in stripper.\nAs this is a blanket error, many factors can influence this error.\nReviewing the actions performed by the stripper prior to the error,\nand reviewing the stripper block may help you identify the issue.',
    'write':'The script has failed writing the stripper fixes into an output .vmf.\nThis is most likely from an oversight within the script itself.\nPlease notify this error if you do encounter it.'
}

#starting messages for error log
def errorInit():
    error.write('Error log for <'+mapname+'>\n')
    error.write('========================================\n')
    error.write('How it works (for stripper blocks):\n')
    error.write('\t* Per stripper block, the script will list all previous actions performed\n')
    error.write('\t* When a fatal error occurs, all actions and the error message are written in this log\n')
    error.write('\t* The entire stripper block is shown afterwards to show where the script has failed\n')
    error.write('\nFor non-stripper errors, only the error message is written in this log.\n')
    error.write('========================================\n')

#append text to error_block
def errorWriteLog(text):
    error_block.append('  '+text)

#print all logs in error_block into error log and print out stripper block
def errorWrite(text,error_type,strip = None):
    global error_count
    error.write('\n-+ Error #'+str(error_count)+' +-\n')
    error.write('----------\n')
    for l in error_block:
        error.write(l+'\n')
    error.write('\n'+text+'\n')
    error.write('\n'+error_dict[error_type]+'\n')
    error.write('\n== Stripper block ==\n')
    if strip:
        writeStripper(error,strip)
    error_count += 1

#so long, cruel world!
def errorFlush():
    global error_block
    error_block = []

#################
#    TESTING    #
#################

#func for testing
def findConflictingLine(name):
    with open('input/'+name+'.vmf','r') as file1:
        with open('output/'+name+'_strip.vmf','r') as file2:
            count = 1
            while True:
                row1 = file1.readline()
                row2 = file2.readline()
                if(row1 != row2):
                    print(count)
                    break
                if(row1 == '' or row2==''):
                    if(row1 != row2):
                        print(count)
                    break
                count += 1

#func for testing
def findEntIdx(k,v):
    for idx, ent in enumerate(ents):
        try:
            if ent[k][k] == v:
                print(idx)
        except:
            continue

#################
#    UTILITY    #
#################

def quitProgram(successful):
    print('========================================')
    if successful:
        printConsole('The program has ended successfully; press enter to exit')
        printLog("End.")
        error.write("\n========================================\n")
        error.write("End.")
        log.close()
        error.close()
        input()
    else:
        printConsole('The program has ended unsuccessfully; press enter to exit')
        printLog("Unsuccessful end.")
        error.write("\n========================================\n")
        error.write("End.")
        log.close()
        error.close()
        input()
        assert False

def printConsole(text):
    print(text+'\n')

def printLog(text):
    log.write(text+'\n')

def appendTab(string,amount):
    return '\t'*amount + string

########################
#    UTILITY - DICT    #
########################

#row has format of "key" "value"
def findKV(row):
    idx = row.find('"')
    count = 0
    k = ''
    v = ''
    while idx >= 0:
        if count==0:
            k = row[idx+1:row.find('"',idx+1)]
        if count==2:
            if (row.find('"',idx+1)) != -1:
                v = row[idx+1:row.find('"',idx+1)]
            #if this row is part of a newlined keyvalue
            else:
                v = row[idx+1:]
        count += 1
        idx = row.find('"',idx+1)
    return k, v

#get key and value in dict format
def getKV(dic):
    return dic['k'],dic[dic['k']]

#check if key exists in dict and returns bool
def checkKeyInDic(dic,key):
    return key in dic

#try modifying key in dict if such exists
#return modified key or NoneType depending on if operation is successful
def modifyKeyInDic(key,value):
    try:
        key = value
        return key
    except:
        return None

#prevent a dict from overriding other existing dict of same key
def returnUniqueName(parent,name):
    count = 0
    unique = name
    while(unique in parent):
        unique = name + str(count)
        count += 1
    return unique

def writeDictKV(k,v):
    return '"'+k+'" "'+v+'"\n'

####################
#    VMF - READ    #
####################

#append ent to keyvalue dictionaries
def addToRefDict(dic):
    if checkKeyInDic(dic,'id'):
        hid = str(dic['id'][dic['id']['k']])
        if not checkKeyInDic(ref['id'],hid):
            ref['id'][hid] = []
        ref['id'][hid].append(dic.copy())
    if checkKeyInDic(dic,'origin'):
        origin = dic['origin'][dic['origin']['k']]
        if not checkKeyInDic(ref['origin'],origin):
            ref['origin'][origin] = []
        ref['origin'][origin].append(dic.copy())
    if checkKeyInDic(dic,'targetname'):
        tname = dic['targetname'][dic['targetname']['k']]
        if not checkKeyInDic(ref['targetname'],tname):
            ref['targetname'][tname] = []
        ref['targetname'][tname].append(dic.copy())
    if checkKeyInDic(dic,'classname'):
        cname = dic['classname'][dic['classname']['k']]
        if not checkKeyInDic(ref['classname'],cname):
            ref['classname'][cname] = []
        ref['classname'][cname].append(dic.copy())
    if checkKeyInDic(dic,'hash'):
        ehash = dic['hash']
        ref['hash'][ehash] = dic.copy()

#separate into separate major vmf blocks
#allows for easier access to entities + prevent potential overflow of world and entity
def appendDict(dic):
    if dic['k'] == 'versioninfo':
        version.append(dic)
    if dic['k'] == 'visgroups':
        vis.append(dic)
    if dic['k'] == 'viewsettings':
        view.append(dic)
    if dic['k'] == 'palette_plus':
        palette.append(dic)
    if dic['k'] == 'colorcorrection_plus':
        cc.append(dic)
    if dic['k'] == 'light_plus':
        light.append(dic)
    if dic['k'] == 'bgimages_plus':
        bg.append(dic)
    if dic['k'] == 'world':
        world.append(dic)
    if dic['k'] == 'entity':
        ents.append(dic)
    if dic['k'] == 'cameras':
        cameras.append(dic)
    if dic['k'] == 'cordons' or dic['k'] == 'cordon':
        cordons.append(dic)

def readVMF(name):
    with open('input/'+name+'.vmf', 'r') as file:
        newline_warning = False
        dic = None
        parent = []
        gen = 0#tracks generations of scopes
        ent_hash = 0
        new_line = False
        for row in file:
            row = row.strip()
            if new_line is True:
                if (row.count('"')==1):
                    k,v = getKV(dic.popitem()[1])
                    v = v+'\\n'+row[0:row.find('"')]
                    unique = returnUniqueName(dic,k)
                    dic[unique] = {'k':k}
                    dic[unique][k] = v
                    new_line = False
                    
                elif (row.count('"')==0):
                    k,v = getKV(dic.popitem()[1])
                    unique = returnUniqueName(dic,k)
                    dic[unique] = {'k':k}
                    dic[unique][k] = v + '\\n' + row
                else:
                    printLog("\n*** ERROR: Stripplier has detected an erroneous line in the .vmf; printing last read line... ***")
                    printLog("\t'"+row+"'")
                    printLog("Stripplier may now be unstable - tread with caution!")
                    dic.popitem()
                    new_line = False
            elif row == '{':
                gen += 1
            elif row == '}':
                gen -= 1
                if(gen > 0):
                    parent[-1][returnUniqueName(parent[-1],dic['k'])] = dic
                    dic = parent.pop()
                else:
                    #enable ents to be filtered with ref dict
                    if dic['k'] == 'entity':
                        dic['hash'] = str(ent_hash)
                        addToRefDict(dic)
                        ent_hash += 1
                    appendDict(dic)
                    dic = None
            #this will be the name of a subscope (e.g. connections:)
            elif row.find('"')==-1:
                if gen > 0:
                    parent.append(dic)
                dic = {'k': row}
            else:
                #newline '\n' detected (CSS vmf) - notify and address issue
                if(row.count('"')==3):
                    if newline_warning is False:
                        printConsole("Newline '\\n' detected: Stripplier will attempt to convert")
                        printConsole("Note: Stripplier natively supports only CS:GO .vmf formats - tread with caution!")
                        printLog("Newline detected in .vmf...")
                        newline_warning = True
                    new_line = True
                k,v = findKV(row)
                unique = returnUniqueName(dic,k)
                dic[unique] = {'k':k}
                dic[unique][k] = v

#####################
#    VMF - WRITE    #
#####################

#writes each block in vmf
def writeScope(file, dic, gen):
    if not dic:
        file.write(appendTab('}',gen))
    for row in dic:
        if row == 'hash':
            continue
        if type(dic[row])==dict:
            #dictionary has more keyvalues other than its name and a dummy kv
            if len(dic[row])>2 or (len(dic[row]) <= 2 and dic[row]['k'] not in dic[row]):
                file.write(appendTab(dic[row]['k']+"\n",gen))
                file.write(appendTab("{\n",gen))
                writeScope(file, dic[row], gen+1)
                file.write(appendTab("}\n",gen))
            else:
                writeScope(file, dic[row], gen)
        elif row!='k':
            file.write(appendTab(writeDictKV(row,dic[row]),gen))
    return file

def writeFile(name):
    with open('output/'+name+'_strip.vmf','w') as file:
        gen = 1
        #gen = 0 reserved for names of major vmf blocks
        for v in version:
            file.write("versioninfo\n")
            file.write("{\n")
            writeScope(file, v, gen)
            file.write("}\n")
        for vi in vis:
            file.write("visgroups\n")
            file.write("{\n")
            writeScope(file, vi, gen)
            file.write("}\n")
        for vie in view:
            file.write("viewsettings\n")
            file.write("{\n")
            writeScope(file, vie, gen)
            file.write("}\n")
        for p in palette:
            file.write("palette_plus\n")
            file.write("{\n")
            writeScope(file, p, gen)
            file.write("}\n")
        for c in cc:
            file.write("colorcorrection_plus\n")
            file.write("{\n")
            writeScope(file, c, gen)
            file.write("}\n")
        for l in light:
            file.write("light_plus\n")
            file.write("{\n")
            writeScope(file, l, gen)
            file.write("}\n")
        for b in bg:
            file.write("bgimages_plus\n")
            file.write("{\n")
            writeScope(file, b, gen)
            file.write("}\n")
        for w in world:
            file.write("world\n")
            file.write("{\n")
            writeScope(file, w, gen)
            file.write("}\n")
        for ent in ents:
            #skip filtered out ents
            if ent != '':
                file.write("entity\n")
                file.write("{\n")
                writeScope(file, ent, gen)
                file.write("}\n")
        for ca in cameras:
            file.write("cameras\n")
            file.write("{\n")
            writeScope(file, ca, gen)
            file.write("}\n")
        for co in cordons:
            file.write("cordons\n")
            file.write("{\n")
            writeScope(file, co, gen)
            file.write("}\n")

#########################
#    STRIPPER - READ    #
#########################

def readStripper(name):
    with open('input/'+name+'.cfg','r') as file:
        dic = None
        parent = []
        gen = 0
        for row in file:
            row = row.strip()
            #ignore comments (may require more character filters)
            if len(row) < 1 or row[0]==';' or row[0]=='/':
                continue
            if row == '{':
                gen += 1
            elif row == '}':
                gen -= 1
                if(gen > 0):
                    parent[-1][returnUniqueName(parent[-1],dic['k'])] = dic
                    dic = parent.pop()
                else:
                    stripper.append(dic)
                    dic = None
            #this will be the name of a subscope (e.g. match:)
            elif row[-1] == ':' and row.find('"')==-1:
                if gen > 0:
                    parent.append(dic)
                dic = {'k': row}
            else:
                k,v = findKV(row)
                #fix small quirk between vmf and stripper formatting
                if k == 'hammerid':
                    k = 'id'
                if isConnectionKV(k,v) and dic['k'] != 'delete:':
                    #fix connection stripper lines that does not specify a delay value
                    v = fixMissingConnectionDelay(v)
                unique = returnUniqueName(dic,k)
                dic[unique] = {'k':k}
                dic[unique][k] = v

#fix potential strippers that does not have any value for the delay value
def fixMissingConnectionDelay(v):
    count = 0
    delim = ['',',']
    for cidx in range(len(v)):
        if count == 3:
            if v[cidx] in delim:
                v = v[:cidx] + '0' + v[cidx:]
            return v
        if v[cidx] in delim:
            count += 1

##########################
#    STRIPPER - WRITE    #
##########################

def writeStripperDict(file,dic):
    file.write(appendTab(dic['k']+'\n',1))
    file.write(appendTab('{\n',1))
    for l in dic:
        if type(dic[l]) == dict:
            k,v = getKV(dic[l])
            if k is not None and v is not None:
                file.write(appendTab(writeDictKV(k,v),2))
            else:
                file.write(appendTab('* THIS STRIPPER LINE COULD NOT BE DISPLAYED *\n',2))
    file.write(appendTab('}\n',1))

def writeStripper(file,strip):
    file.write(strip['k']+'\n')
    file.write('{\n')
    for b in strip:
        if type(strip[b]) == dict:
            if dict in [type(strip[b][x]) for x in strip[b]]:
                writeStripperDict(file,strip[b])
            else:
                k,v = getKV(strip[b])
                file.write(appendTab(writeDictKV(k,v),1))
    file.write('}\n')

#############
#    BSP    #
#############

def readBSP(name):
    with open('input/'+name+'.bsp','r',errors='ignore') as file:
        read_file = False
        read_block = True
        model_id = None
        for row in file:
            row = row.strip()
            if row.find("world_maxs") != -1:
                read_file = True
            elif read_file:
                if row == '}':
                    if read_block:
                        read_block = False
                        model_id = None
                    #should have reached end of ent lump in bsp
                    else:
                        return
                elif row == '{':
                    if not read_block:
                        read_block = True
                    #should have reached end of ent lump in bsp
                    else:
                        return
                elif read_file:
                    if row.find('"model"') != -1 and row.find('*') != -1:
                        _,model_id = findKV(row)
                    elif row.find('"hammerid"') != -1 and model_id:
                        _,hid = findKV(row)
                        try:
                            ref['model'][model_id] = ref['id'][hid]
                        except:
                            pass

##################
#    PRINTING    #
##################

#print info of match: block in a stripper block
def printStripperMatch(strip):
    printLog('-----')
    printLog(strip['k'][:-1].capitalize()+'ing entity/entities with keyvalues of:')
    if strip['k'] == 'modify:':
        for m in strip['match:']:
            if m != 'k':
                printLog('  "'+strip['match:'][m]['k']+'" "'+strip['match:'][m][strip['match:'][m]['k']]+'"')
    #for add: stripper blocks
    else:
        for m in strip:
            if m != 'k':
                printLog('  "'+strip[m]['k']+'" "'+strip[m][strip[m]['k']]+'"')

#print specific info of ents - keys may be changed at own discretion
def printEntityInfo(ent):
    key = ['classname','targetname','origin','id']
    for k in key:
        if k in ent:
            printLog('\t  "'+k+'" "'+ent[k][k]+'"')

#print kv's changed by stripper
def printStripperModifications(strip):
    printLog('')
    for b in strip:
        if b != 'k' and b != 'match:':
            #replaceing
            if b == 'replace:':
                printLog('By '+b[:6]+'ing:')
            else:
                printLog('By '+b[:-1]+'ing:')
            for k in strip[b]:
                if k != 'k':
                    printLog('  "'+strip[b][k]['k']+'" "'+strip[b][k][strip[b][k]['k']]+'"')

################
#    VECTOR    #
################

#change coords in string format "x y z" into vector dict
def strToVec(string):
    coord = {'x':0,'y':0,'z':0}
    idx = 0
    for d in coord:
        if string.find(' ',idx+1) != -1:
            coord[d] = float(string[idx:string.find(' ',idx+1)])
        else:
            coord[d] = float(string[idx:])
        idx = string.find(' ',idx+1)
    return coord

#reverse of above
def vecToStr(vector):
    return str(vector['x'])+" "+str(vector['y'])+" "+str(vector['z'])

#from vec1 to vec2
#round to 3 decimal places to prevent float imprecisions
def vecDist(vec1,vec2):
    return {'x':round(vec2['x']-vec1['x'],3),'y':round(vec2['y']-vec1['y'],3),'z':round(vec2['z']-vec1['z'],3)}

#isint = True if the output has to be in integer format
#round to 3 decimal places to prevent float imprecisions
def vecAdd(vec1,vec2):
    temp = {'x':round(vec2['x']+vec1['x'],3),'y':round(vec2['y']+vec1['y'],3),'z':round(vec2['z']+vec1['z'],3)}
    return temp

###############
#    SOLID    #
###############

#shift plane [which has format of '(x1 y1 z1) (x2 y2 z2) (x3 y3 z3)'] by a specified vector
def shiftPlane(plane, dist):
    bra = plane.find('(')
    ket = plane.find(')')
    new = ''
    while True:
        new += '('
        new += vecToStr(vecAdd(strToVec(plane[bra+1:ket]),dist))
        new += ')'
        bra = plane.find('(',bra+1)
        if bra < 0:
            break
        ket = plane.find(')',ket+1)
        new += ' '
    return new

#duplicate side of a solid
def duplicateSolidSide(side):
    dupe = {}
    for k in side:
        if k != 'id':
            #skip h++ exclusive properties for backwards compatiability
            try:
                if k == 'vertices_plus':
                    continue
            except:
                pass
            if k == 'k':
                dupe[k] = 'side'
            elif len(side[k]) <= 2:
                dupe[k] = {'k':side[k]['k'],side[k]['k']:side[k][side[k]['k']]}
            #vertices_plus block is h++ specific feature, this will be skipped in normal non-h++ vmf
            else:
                dupe[k] = {'k':'vertices_plus'}
                for v in side[k]:
                    if v != 'k':
                        dupe[k][v] = {'k':side[k][v]['k'],side[k][v]['k']:side[k][v][side[k][v]['k']]}
    return dupe

#duplicate the geometry of a given ent to a new origin
def duplicateEntFunc(ent, new_origin):
    dist = vecDist(strToVec(ent['origin']['origin']),strToVec(new_origin))
    new = {'solid':{'k':'solid'}}
    new['editor'] = stripperEditor({})
    for row in ent['solid']:
        if row == 'editor':
            new['solid'][row] = stripperEditor({})
        elif row == 'k':
            new['solid']['k'] = 'solid'
        elif row == 'id':
            continue
        #create 6 sides of the solid
        else:
            new['solid'][row] = duplicateSolidSide(ent['solid'][row])
            new['solid'][row]['plane'] = {'k':'plane','plane':shiftPlane(ent['solid'][row]['plane']['plane'],dist)}
            #if vmf uses h++ features, try to copy the block
            try:
                for v in new['solid'][row]['vertices_plus']:
                    if v != 'k':
                        new['solid'][row]['vertices_plus'][v]['v'] = vecToStr(vecAdd(strToVec(new['solid'][row]['vertices_plus'][v]['v']),dist))
            except:
                pass
    new['strippered'] = {'k':'strippered','strippered':'1'}
    return new

#create a default side of a solid
#assumed created func is likely to be a trigger
def createSolidSide():
    return {'k':'side','material':{'k':'material','material':'TOOLS/TOOLSTRIGGER'},'rotation':{'k':'rotation','rotation':'0'},'lightmapscale':{'k':'lightmapscale','lightmapscale':'16'},'smoothing_groups':{'k':'smoothing_groups','smoothing_groups':'0'}}

#try to find if there is logic_auto/logic_relay/whatever else that defines boundary size of the new trigger/func brush
def findSolidBoundary(ent_name, ent_origin):
    mins = None
    maxs = None
    target = []
    for s in stripper:
        if mins and maxs:
            break
        #try to look at the same stripper block first (add: type)
        try:
            if s['targetname']['targetname'] == ent_name:
                for l in s:
                    try:
                        if s[l][s[l]['k']].find('!self') == 0 and s[l][s[l]['k']].find('mins') != -1:
                            mins = strToVec(findCoordFromInsert(s[l][s[l]['k']][s[l][s[l]['k']].find('mins')+5:]))
                            if s not in target:
                                target.append(s)
                        elif s[l][s[l]['k']].find('!self') == 0 and s[l][s[l]['k']].find('maxs') != -1:
                            maxs = strToVec(findCoordFromInsert(s[l][s[l]['k']][s[l][s[l]['k']].find('maxs')+5:]))
                            if s not in target:
                                target.append(s)
                    except:
                        pass
        except:
            pass
        #stripper is of modify: type
        if s['k'] == 'modify:':
            try:
                for i in [x for x in s['insert:'] if type(s['insert:'][x])==dict]:
                    if mins and maxs:
                        break
                    _,ival = getKV(s['insert:'][i])
                    if ival.find(ent_name) == 0:
                        if ival.find('mins') != -1:
                            mins = strToVec(findCoordFromInsert(ival[ival.find('mins')+5:]))
                            if s not in target:
                                target.append(s)
                        if ival.find('maxs') != -1:
                            maxs = strToVec(findCoordFromInsert(ival[ival.find('maxs')+5:]))
                            if s not in target:
                                target.append(s)
            except:
                pass
        #stripper is of add: type
        elif s['k'] == 'add:':
            try:
                for i in [x for x in s if type(s[x])==dict]:
                    if mins and maxs:
                        break
                    _,ival = getKV(s[i])
                    if ival.find(ent_name) == 0:
                        if ival.find('mins') != -1:
                            mins = strToVec(findCoordFromInsert(ival[ival.find('mins')+5:]))
                            if s not in target:
                                target.append(s)
                        if ival.find('maxs') != -1:
                            maxs = strToVec(findCoordFromInsert(ival[ival.find('maxs')+5:]))
                            if s not in target:
                                target.append(s)
            except:
                pass
    #if all fails then assign default volume of +-100 to each dimension
    if not mins or not maxs:
        mins = vecAdd(strToVec(ent_origin),{'x':-100,'y':-100,'z':-100})
        maxs = vecAdd(strToVec(ent_origin),{'x':100,'y':100,'z':100})
    #if mins/maxs was found apply it to newly created func's origin
    else:
        mins = vecAdd(strToVec(ent_origin),mins)
        maxs = vecAdd(strToVec(ent_origin),maxs)
    return mins, maxs, target

#create a solid for a brush
def createSolid(ent,mins=None,maxs=None,target=None):
    errorWriteLog('Creating new solid from a given ent')
    if not mins and not maxs and not target:
        errorWriteLog('Trying to find replacement volume')
        try:
            mins, maxs, target = findSolidBoundary(ent['targetname']['targetname'],ent['origin']['origin'])
        #some added func ents may not have an origin stated within the stripper
        except:
            printLog('\n*** WARNING: A new func entity has not been given an origin - giving default origin of "0 0 0" instead ***')
            mins, maxs, target = findSolidBoundary(ent['targetname']['targetname'],'0 0 0')
        printLog('\nThis entity will have a minimum and maximum boundary of:')
        printLog('\t"mins" "'+str(mins['x'])+' '+str(mins['y'])+' '+str(mins['z'])+'"')
        printLog('\t"maxs" "'+str(maxs['x'])+' '+str(maxs['y'])+' '+str(maxs['z'])+'"')
        printLog('\nWhere the boundaries were provided in a stripper block for:')
        if len(target)>0:
            errorWriteLog('Replacement volume found')
            for t in target:
                try:
                    for m in t['match:']:
                        if m != 'k':
                            printLog('  "'+m+'" "'+t['match:'][m][t['match:'][m]['k']]+'"')
                except:
                    for m in t:
                        if m =='classname' or m =='targetname' or m == 'origin' or m == 'id':
                            printLog('  "'+m+'" "'+t[m][t[m]['k']]+'"')
        else:
            printLog('\t*** WARNING: No other stripper block provided boundaries for this entity ***')
            printLog('\tA default bounday of +-100 in every dimension from the entity origin is given instead')
            errorWriteLog('Replacement volume NOT found - defaulting to +-100 in all dimensions')
    solid = {'k':'solid','editor':stripperEditor({})}
    #assume rectangular solid being created
    for f in range(6):
        side = createSolidSide()
        #-x normal face
        if f == 0:
            side['plane'] = {'k':'plane','plane':'('+str(mins['x'])+' '+str(maxs['y'])+' '+str(mins['z'])+') ('+str(mins['x'])+' '+str(maxs['y'])+' '+str(maxs['z'])+') ('+str(mins['x'])+' '+str(mins['y'])+' '+str(maxs['z'])+')'}
            side['uaxis'] = {'k':'uaxis','uaxis':'[0 -1 0 0] 0.25'}
            side['vaxis'] = {'k':'vaxis','vaxis':'[0 0 -1 0] 0.25'}
        #+x normal face
        if f == 1:
            side['plane'] = {'k':'plane','plane':'('+str(maxs['x'])+' '+str(mins['y'])+' '+str(mins['z'])+') ('+str(maxs['x'])+' '+str(mins['y'])+' '+str(maxs['z'])+') ('+str(maxs['x'])+' '+str(maxs['y'])+' '+str(maxs['z'])+')'}
            side['uaxis'] = {'k':'uaxis','uaxis':'[0 1 0 0] 0.25'}
            side['vaxis'] = {'k':'vaxis','vaxis':'[0 0 -1 0] 0.25'}
        #-y normal face
        if f == 2:
            side['plane'] = {'k':'plane','plane':'('+str(mins['x'])+' '+str(mins['y'])+' '+str(mins['z'])+') ('+str(mins['x'])+' '+str(mins['y'])+' '+str(maxs['z'])+') ('+str(maxs['x'])+' '+str(mins['y'])+' '+str(maxs['z'])+')'}
            side['uaxis'] = {'k':'uaxis','uaxis':'[1 0 0 0] 0.25'}
            side['vaxis'] = {'k':'vaxis','vaxis':'[0 0 -1 0] 0.25'}
        #+y normal face
        if f == 3:
            side['plane'] = {'k':'plane','plane':'('+str(maxs['x'])+' '+str(maxs['y'])+' '+str(mins['z'])+') ('+str(maxs['x'])+' '+str(maxs['y'])+' '+str(maxs['z'])+') ('+str(mins['x'])+' '+str(maxs['y'])+' '+str(maxs['z'])+')'}
            side['uaxis'] = {'k':'uaxis','uaxis':'[-1 0 0 0] 0.25'}
            side['vaxis'] = {'k':'vaxis','vaxis':'[0 0 -1 0] 0.25'}
        #-z normal face
        if f == 4:
            side['plane'] = {'k':'plane','plane':'('+str(mins['x'])+' '+str(maxs['y'])+' '+str(mins['z'])+') ('+str(mins['x'])+' '+str(mins['y'])+' '+str(mins['z'])+') ('+str(maxs['x'])+' '+str(mins['y'])+' '+str(mins['z'])+')'}
            side['uaxis'] = {'k':'uaxis','uaxis':'[-1 0 0 0] 0.25'}
            side['vaxis'] = {'k':'vaxis','vaxis':'[0 -1 0 0] 0.25'}
        #+z normal face
        if f == 5:
            side['plane'] = {'k':'plane','plane':'('+str(mins['x'])+' '+str(mins['y'])+' '+str(maxs['z'])+') ('+str(mins['x'])+' '+str(maxs['y'])+' '+str(maxs['z'])+') ('+str(maxs['x'])+' '+str(maxs['y'])+' '+str(maxs['z'])+')'}
            side['uaxis'] = {'k':'uaxis','uaxis':'[1 0 0 0] 0.25'}
            side['vaxis'] = {'k':'vaxis','vaxis':'[0 -1 0 0] 0.25'}
        solid['side'+str(f)] = side
    return solid

############################
#    STRIPPER - UTILITY    #
############################

def isNumericOrWS(char):
    return True if ord(char) == 45 or ord(char) == 46 or ord(char) == 32 or (ord(char)>=48 and ord(char)<=57) else False

#assume all regex starts and end with '/'
def isRegex(value):
    return True if (value[0] == '/' and value[-1] == '/') else False

#assume all connection kv has 'On...','Pressed...','Out...' key that has ','/'' in value
def isConnectionKV(k,v):
    return True if (len([x for x in ['On','Pressed','Out'] if k.find(x) == 0]) > 0 and not (v.find(',') == -1 and v.find('') == -1)) else False

#change kv inside editor block to let know the ent is from a stripper fix
def stripperEditor(editor):
    editor['color'] = {'k':'color','color':'0 0 255'}
    editor['comments'] = {'k':'comments','comments':'Stripper fixed'}
    editor['k'] = 'editor'
    return editor

#find ent by model number
def findEntFunc(model):
    try:
        ent = ref['model'][model][0]
        return ent
    except:
        return None

#try to find coordinates from an insert: line
#to be used to find mins/maxs boundary of new func ent
def findCoordFromInsert(partial):
    coord = ''
    for c in partial:
        if isNumericOrWS(c):
            coord += c
        else:
            return coord

###########################
#    STRIPPER - SEARCH    #
###########################

#bool on if given connection kv is present in the targetted ent
#isRegex given as bool
def stripperConnectionKVInEnt(key,value,connections,isRegex):
    for c in connections:
        if type(connections[c]) == dict:
            ckey,cval = getKV(connections[c])
            if isRegex:
                if ckey.lower() == key.lower() and re.search(value[1:-1],cval, re.IGNORECASE):
                    return True
            else:
                if ckey.lower() == key.lower() and cval.lower() == value.lower():
                    return True
    return False

#find ents in modified ents array
#last resort search that should be called if no ent was found!
def stripperForceFindMatch(targets_copy,k,v):
    targets = []
    #go through all recorded ents
    for e in ents:
        #normal kv
        if not isConnectionKV(k,v) and k in e:
            _,rval = getKV(e[k])
            if isRegex(v):
                if re.search(v[1:-1],rval, re.IGNORECASE):
                    #see if ent is also a targetted ent
                    if len(targets_copy) > 0:
                        if e['hash'] in [x['hash'] for x in targets_copy if x['hash']==e['hash']]:
                            targets.append(e.copy())
                    #there are no targetted ents yet
                    else:
                        targets.append(e.copy())
            else:
                if v == rval:
                    #see if ent is also a targetted ent
                    if len(targets_copy) > 0:
                        if e['hash'] in [x['hash'] for x in targets_copy if x['hash']==e['hash']]:
                            targets.append(e.copy())
                    #there are no targetted ents yet
                    else:
                        targets.append(e.copy())
        #conneciton kv
        elif 'connections' in e:
            if isRegex(v):
                if stripperConnectionKVInEnt(k,v,e['connections'],True):
                    #see if ent is also a targetted ent
                    if len(targets_copy) > 0:
                        if e['hash'] in [x['hash'] for x in targets_copy if x['hash']==e['hash']]:
                            targets.append(e.copy())
                    #there are no targetted ents yet
                    else:
                        targets.append(e.copy())
            else:
                if stripperConnectionKVInEnt(k,v,e['connections'],False):
                    #see if ent is also a targetted ent
                    if len(targets_copy) > 0:
                        if e['hash'] in [x['hash'] for x in targets_copy if x['hash']==e['hash']]:
                            targets.append(e.copy())
                    #there are no targetted ents yet
                    else:
                        targets.append(e.copy())
    return targets

#find ents in stripper match
def stripperFindMatch(match):
    errorWriteLog('Start to look for entity targets')
    targets = []
    reserved_k = ['model','id','origin','targetname','classname']
    #first go through fast searches with ref dict
    #these keyvalues are unique, so no need to care for dictionary naming convention
    for k in reserved_k:
        if k in match:
            targets_copy = targets.copy()
            #not model number but model path
            if k == 'model' and match[k][match[k]['k']][0] != '*':
                continue
            k,v = getKV(match[k])
            try:
                errorWriteLog('Target entities with [ "'+k+'" "'+v+'" ]')
            except:
                errorWriteLog('An exception occured while writing an action to the error log!')
                return
            #first batch of targets
            if len(targets) < 1:
                errorWriteLog('No previous targets found, starting new target array')
                if isRegex(v):
                    for r in ref[k]:
                        if re.search(v[1:-1],r, re.IGNORECASE):
                            targets.append(ref[k][r][0])
                else:
                    try:
                        targets = ref[k][v]
                        continue
                    except:
                        printLog('\t*** Keyvalue ["'+k+'" "'+v+'"] could not found be in vmf ***')
                        printLog('\t*** Trying to perform case-insensitive search... ***')
                        errorWriteLog('Possible case-sensitive issues - trying to remedy')
                    #consider incorrect cases on values
                    for e in ref[k]:
                        if v.lower() == e.lower():
                            targets = ref[k][e]
                            continue
            #potential targets already exist
            else:
                errorWriteLog('Previous targets found, filter entities from this array')
                matching = []
                for idx,t in enumerate(targets):
                    if k in t:
                        #change string to 3d vector for origin comparisons
                        if k == 'origin':
                            #surely you wouldn't use regex for 'origin' :clueless:
                            if strToVec(t[k][t[k]['k']]) == strToVec(v):
                                matching.append(t)
                        else:
                            if isRegex(v):
                                if re.search(v[1:-1],t[k][t[k]['k']], re.IGNORECASE):
                                    matching.append(t)
                            else:
                                if t[k][t[k]['k']].lower() == v.lower():
                                    matching.append(t)
                targets = matching
            #No ent has been found
            if len(targets) == 0:
                printLog('\t*** No entity has been matched in the original vmf ***')
                printLog('\t*** Trying search amongst stripper modified/added ents... ***')
                errorWriteLog('No entities found - try searching on stripper modified ents')
                targets = stripperForceFindMatch(targets_copy,k,v)
                #No ent, either in original or modified state, has been found
                if len(targets) == 0:
                    errorWriteLog('No entities found - returning')
                    return []
    #go through other keyvalues
    for m in match:
        #go through other keys in match:
        #look through model again for model path (not model number) searches
        if type(match[m]) == dict and match[m]['k'] not in reserved_k[1:]:
            #if model is model number then skip
            if m == 'model' and match[m][match[m]['k']][0] == '*':
                continue
            k,v = getKV(match[m])#need key in this case as there may be multiple lines trying to stripper a same key (e.g. connection kv)
            try:
                errorWriteLog('Target entities with [ "'+k+'" "'+v+'" ]')
            except:
                errorWriteLog('An exception occured while writing an action to the error log!')
                return
            targets_copy = targets.copy()
            #first batch of targets
            if len(targets) < 1:
                errorWriteLog('No previous targets found, starting new target array')
                add = []
                #go through all recorded ents
                for e in ref['hash']:
                    #normal kv
                    if not isConnectionKV(k,v) and m in ref['hash'][e]:
                        _,rval = getKV(ref['hash'][e][m])
                        if isRegex(v):
                            if re.search(v[1:-1],rval, re.IGNORECASE):
                                add.append(ref['hash'][e])
                        else:
                            if v.lower() == rval.lower():
                                add.append(ref['hash'][e])
                    #conneciton kv
                    elif 'connections' in ref['hash'][e]:
                        if isRegex(v):
                            if stripperConnectionKVInEnt(k,v,ref['hash'][e]['connections'],True):
                                add.append(ref['hash'][e])
                        else:
                            if stripperConnectionKVInEnt(k,v,ref['hash'][e]['connections'],False):
                                add.append(ref['hash'][e])
                targets = add
            #potential targets already exist
            else:
                errorWriteLog('Previous targets found, filter entities from this array')
                matching = []
                #go through potential ents
                for idx,t in enumerate(targets):
                    #normal kv
                    if not isConnectionKV(k,v):
                        if m in t:
                            if isRegex(v):
                                if re.search(v[1:-1],t[k][t[k]['k']], re.IGNORECASE):
                                    matching.append(t)
                            else:
                                if t[k][t[k]['k']].lower() == v.lower():
                                    matching.append(t)
                    #connection kv
                    elif 'connections' in t:
                        if isRegex(v):
                            if stripperConnectionKVInEnt(k,v,t['connections'],True):
                                matching.append(t)
                        else:
                            if stripperConnectionKVInEnt(k,v,t['connections'],False):
                                matching.append(t)
                targets = matching
        #No ent has been found
            if len(targets) == 0:
                printLog('\t*** No entity has been matched in the original vmf ***')
                printLog('\t*** Trying search amongst stripper modified/added ents... ***')
                errorWriteLog('No entities found - try searching on stripper modified ents')
                targets = stripperForceFindMatch(targets_copy,k,v)
                #No ent, either in original or modified state, has been found
                if len(targets) == 0:
                    errorWriteLog('No entities found - returning')
                    return []
    return targets

###########################
#    STRIPPER - DELETE    #
###########################

#if a model number is being deleted, check if the same stripper defines a new boundary to substitue via insert:
#returns if this has been successful or not
def stripperDeleteModel(ent, insert):
    origin = None
    mins = None
    maxs = None
    while not origin and not mins and not maxs:
        for i in insert:
            if type(insert[i]) == dict:
                key, value = getKV(insert[i])
                if value.find('mins') != -1:
                    mins = strToVec(findCoordFromInsert(value[value.find('mins')+5:]))
                    errorWriteLog('Replacement minimum coordinates found')
                elif value.find('maxs') != -1:
                    maxs = strToVec(findCoordFromInsert(value[value.find('maxs')+5:]))
                    errorWriteLog('Replacement maximum coordinates found')
                elif value.find('origin') != -1:
                    origin = strToVec(findCoordFromInsert(value[value.find('origin')+6:]))
                    errorWriteLog('Replacement origin coordinates found')
        break
    if mins and maxs:
        printLog('\nDeleting model kv by replacing entity volume with the following boundaries:')
        errorWriteLog('Minimum and maximum coords found - attempt replacing volume')
        if not origin:
            errorWriteLog('Replacement origin coords not found')
            if 'origin' in ent:
                printLog('\tNo changes in origin found - assuming origin will stay unchanged')
                errorWriteLog('Using origin of the original entity')
                origin = strToVec(ent['origin']['origin'])
            else:
                printLog('\tNo information about origin found - defaulting to world origin')
                errorWriteLog('Defaulting to world origin')
                ent['origin']['origin'] = '0 0 0'
                origin = strToVec(ent['origin']['origin'])
        mins = vecAdd(mins, origin)
        maxs = vecAdd(maxs, origin)
        ent['origin']['origin'] = vecToStr(origin)
        printLog('\t"origin" "'+str(origin['x'])+' '+str(origin['y'])+' '+str(origin['z'])+'"')
        printLog('\t"mins" "'+str(mins['x'])+' '+str(mins['y'])+' '+str(mins['z'])+'"')
        printLog('\t"maxs" "'+str(maxs['x'])+' '+str(maxs['y'])+' '+str(maxs['z'])+'"')
        ent['solid'] = createSolid(ent,mins,maxs,None)
        return ent, insert
    else:
        printLog('\n*** WARNING: Attempting to delete model number but no valid volume substitution has been found ***')
        return None

#perform delete:
def stripperDelete(ent, delete, d, insert):
    try:
        key, value = getKV(delete[d])
        try:
            errorWriteLog('Deleting [ "'+key+'" "'+value+'" ]')
        except:
            errorWriteLog('An exception occured while writing an action to the error log!')
            return
        #regex
        if isRegex(value):
            errorWriteLog('(Regex detected)')
            del_idx = []
            for t in ent['connections']:
                if type(ent['connections'][t]) == dict:
                    if re.search(value[1:-1],ent['connections'][t][ent['connections'][t]['k']], re.IGNORECASE):
                        del_idx.append(t)
            for d in del_idx:
                del ent['connections'][d]
        #normal kv
        elif not isConnectionKV(key,value):
            errorWriteLog('(Normal keyvalue)')
            #only attempt to delete model number if:
            #   * model is in model number format
            #   * stripper targetted ent already has a solid
            #   * stripper targetted ent has an origin
            if d == 'model' and 'solid' in ent and 'origin' in ent and delete[d][delete[d]['k']][0] == '*':
                errorWriteLog('Attempting to delete by model number - try to find replacement volume')
                ent, insert = stripperDeleteModel(ent, insert)
            else:
                del ent[d]
        #connections kv
        else:
            errorWriteLog('(Connection keyvalue)')
            for t in ent['connections']:
                if type(ent['connections'][t]) == dict:
                    if re.sub(r'[,]+','',ent['connections'][t][ent['connections'][t]['k']]) == re.sub(r'[,]+','',value):
                        del ent['connections'][t]
                        break
    except:
        printLog('\n*** WARNING: Attempting to delete an invalid keyvalue pair [ "'+key+'" "'+value+'" ] - is this intentional? ***\n')

###########################
#    STRIPPER - INSERT    #
###########################

#perform insert:
def stripperInsert(ent, insert, i):
    #normal kv
    key, value = getKV(insert[i])
    try:
        errorWriteLog('Inserting [ "'+key+'" "'+value+'" ]')
    except:
        errorWriteLog('An exception occured while writing an action to the error log!')
        return
    if not isConnectionKV(key,value):
        errorWriteLog('(Normal keyvalue)')
        ent[i] = {'k':key,key:value}
    #connection kv
    else:
        #ent may not already have 'connections' dict created
        errorWriteLog('(Connection keyvalue)')
        try:
            ent['connections']
        except:
            ent['connections'] = {'k':'connections'}
        ent['connections'][returnUniqueName(ent['connections'],key)] = {'k':key,key:value}
    return ent

############################
#    STRIPPER - REPLACE    #
############################

def stripperReplace(ent,replace,r):
    if r != 'k':
        k,v = getKV(replace[r])
        try:
            errorWriteLog('Replacing [ "'+k+'" "'+v+'" ]')
        except:
            errorWriteLog('An exception occured while writing an action to the error log!')
            return
        #only attempt to replace model number if:
        #   * model is in model number format
        #   * stripper targetted ent already has a solid
        #   * stripper targetted ent has an origin
        if r == 'model' and 'solid' in ent and 'origin' in ent and v[0] == '*':
            
            printLog('\nReplacing model kv by duplicating entity volume from the following entity:')
            errorWriteLog('Replace by model number kv detected')
            replacement = findEntFunc(v)
            if replacement:
                ent['solid'] = duplicateEntFunc(replacement,ent['origin']['origin'])['solid']
                errorWriteLog('Replacement solid found')
                printEntityInfo(replacement)
            else:
                printLog('\n*** WARNING: An entity with model number [ "'+k+'" "'+v+'" ] has not been found ***')
                errorWriteLog('Replacement solid NOT found')
        else:
            try:
                ent[r][ent[r]['k']] = v
            #some kv with default values (e.g. spawnflag 0) may not be defined in .vmf - perform insert: in this case
            except:
                errorWriteLog('Replcing keyvalue not found - attempt to insert instead')
                printLog('\n*** WARNING: The keyvalue pair [ "'+k+'" "'+v+'" ] could not be replaced - attempting to insert instead ***\n')
                stripperInsert(ent,replace,r)

###########################
#    STRIPPER - MODIFY    #
###########################

#perform modify:
def stripperStrip(ent_hash,insert,replace,delete):
    ent = ents[ent_hash]
    #targetted ent has been deleted by stripper
    if ent == "":
        return
    #perform delete:
    if delete:
        errorWriteLog('Start to apply delete:')
        for d in delete:
            if d != 'k':
                stripperDelete(ent,delete,d,insert)
    if insert:
        errorWriteLog('Start to apply insert:')
        for i in insert:
            if i != 'k':
                stripperInsert(ent,insert,i)
    if replace:
        errorWriteLog('Start to apply replace:')
        for r in replace:
            stripperReplace(ent,replace,r)
    #Add messages about stripplier if the ent already makes use of hammer editor
    #features
    try:
        ent['editor'] = stripperEditor(ent['editor'])
    except:
        pass
    ent['strippered'] = {'k':'strippered','strippered':'1'}

#find ents matching with match: and perform modify: on targetted ents
def stripperModify(strip):
    printLog('\nThis will modify the following entity/entities:')
    targets = stripperFindMatch(strip['match:'])
    if len(targets) > 0:
        errorWriteLog(str(len(targets))+' entities found - attempting to apply stripper')
        insert = None
        replace = None
        delete = None
        for b in strip:
            if b != 'match:' and type(strip[b]) == dict:
                if b == 'insert:':
                    insert = strip[b]
                elif b == 'replace:':
                    replace = strip[b]
                elif b == 'delete:':
                    delete = strip[b]
        #strip the ent
        for idx,t in enumerate(targets):
            printLog('\tEntity '+str(idx+1)+':')
            printEntityInfo(t)
            errorWriteLog('Attempt to apply stripper on target entity #'+str(idx+1))
            stripperStrip(int(t['hash']), insert, replace, delete)
    #no ents were stripped
    else:
        printLog('\t*** WARNING: No valid entity has been targetted! ***')
    try:
        printStripperModifications(strip)
    except:
        printLog('\t*** ERROR: The stripper block could not be displayed ***')
        errorWrite('*** ERROR: The stripper block could not be displayed ***','stripper',strip)

########################
#    STRIPPER - ADD    #
########################

#perform add:
def stripperAdd(strip):
    ent = {}
    dupe = False
    try:
        #assume add: with model number is duplication of existing brush
        if strip['model']['model'].find('*')!=-1:
            errorWriteLog('Adding by model number keyvalue detected')
            dupe = True
    except:
        dupe = False
    connections = {'k':'connections'}
    #need to create fresh ent
    if not dupe:
        errorWriteLog('Attempting add a new entity')
        #add kv
        for k in strip:
            if type(strip[k]) == dict:
                #normal kv
                key, value = getKV(strip[k])
                if not isConnectionKV(key,value):
                    ent[k] = {'k':key, key:value}
                #connection kv
                else:
                    connections[k] = {'k':key, key:value}
        ent['editor'] = stripperEditor({})
        #append connection dict if a/multiple connection kv exist(s)
        if(len(connections)>1):
            ent['connections'] = connections
        #if it is a trigger_ or func_, a 3d brush is also necessary
        if ent['classname']['classname'].find('trigger_') == 0 or ent['classname']['classname'].find('func_') == 0:
            errorWriteLog('The new entity is a func entity - attempting to find a suitable volume')
            ent['solid'] = createSolid(ent,None,None,None)
    #need to duplicate from an existing ent
    else:
        printLog('\nThis entity will copy the solid(/brush) of the following entity:')
        errorWriteLog('Attempting to duplicate solid from an existing entity')
        target = findEntFunc(strip['model']['model'])
        #model number does not exist in bsp
        if not target:
            errorWriteLog('Targetted model number entity NOT found')
            printLog('\n*** ERROR: a solid(/brush) with model number "'+strip['model']['model']+'" has not been found ***')
        printEntityInfo(target)
        errorWriteLog('Targetted model number entity found')
        if ents[int(target['hash'])] == '':
            printLog('\t* Note: This entity has been filtered by a previous block *')
            errorWriteLog('Targetted entity is previously stripper added')
        #duplicate info about brush solid
        ent = duplicateEntFunc(target,strip['origin']['origin'])
        #add kv
        for k in strip:
            if k != 'k' and k != 'model':
                key, value = getKV(strip[k])
                #normal kv
                if not isConnectionKV(key,value):
                    ent[k] = {'k':key, key:value}
                #connection kv
                else:
                    connections[k] = {'k':key, key:value}
        #append connection dict if a/multiple connection kv exist(s)
        if(len(connections)>1):
            ent['connections'] = connections
    ent['k'] = 'entity'
    ent['strippered'] = {'k':'strippered','strippered':'1'}
    ent['hash'] = str(len(ents))
    addToRefDict(ent.copy())
    ents.append(ent)

###########################
#    STRIPPER - FILTER    #
###########################

#perform filter:
def stripperFilter(strip):
    printLog('\nThis will delete the following entity/entities:')
    targets = stripperFindMatch(strip)
    #go through all ents to be deleted, print their info and 'delete' them
    #we just blank out those ents in the list so that we can still index easily by hash
    if len(targets) < 1:
        printLog('\t*** WARNING: No valid entity has been targetted! ***')
        errorWriteLog('No entity to filter by')
    else:
        errorWriteLog('Filter entities found, trying to filter...')
        for idx,t in enumerate(targets):
            printLog('\tEntity '+str(idx+1)+':')
            printEntityInfo(t)
            ents[int(t['hash'])] = ""

#########################
#    STRIPPER - MAIN    #
#########################


#perform actions of each stripper block
def stripperApply():
    count = 1
    for strip in stripper:
        printLog('-+ Stripper Block #'+str(count)+' +-')
        printConsole('-+ Working stripper block #'+str(count)+' +-')
        errorWriteLog('Starting stripper block #'+str(count))
        printStripperMatch(strip)
        try:
            if strip['k']=='modify:':
                errorWriteLog('Stripper block modify: type - attempt to modify...')
                stripperModify(strip)
            elif strip['k']=='add:':
                errorWriteLog('Stripper block add: type - attempt to add...')
                stripperAdd(strip)
            elif strip['k']=='filter:':
                errorWriteLog('Stripper block filter: type - attempt to filter...')
                stripperFilter(strip)
        except:
            printConsole('ERROR: stripper block could not be applied - skipping')
            printLog("\n*** ERROR: stripper block could not be applied - skipping ***")
            errorWrite("*** ERROR: stripper block could not be applied - skipping ***",'stripper',strip)
        printLog('\n')
        errorFlush()
        count += 1

##############
#    INIT    #
##############

printConsole('Stripplier v2.0.2')
printConsole('Made for Source 2 Zombie Escape (S2ZE) <https://github.com/Source2ZE>')
printConsole('========================================')
printConsole('Instructions:')
printConsole('\t1) Create an input folder relative to .exe path')
printConsole('\t\te.g. if the path to .exe is .../folder/, create an input folder such that .../folder/input')
printConsole('\t2) Put the .vmf, .cfg, and .bsp files into the input folder')
printConsole('\t\tIMPORTANT: Make sure all files have the same name and letter cases!')
printConsole('\t3) Type in the map name without any file extensions (e.g. ze_map_name_final_version_xd)')
printConsole('\t4) A strippered vmf and a log file will be created in the output folder after execution')
printConsole('\t5) Access strippered ents in hammer by filtering with "strippered" "1" in Entity Report menu')
printConsole('\nNote:')
printConsole('\t* It is recommended that you save the input vmf at least once in hammer beforehand')
printConsole('\t* The output log file can be filtered by ERROR: for any stripper block implementation failures')
printConsole('\t   or WARNING: for any miscellaneous issues that may require your attention')
printConsole('\t* For certain cases manual work is still necessary')
printConsole('\t\te.g. any stripper modifications made to the compiled brush number')
printConsole('\t* The tool does not check if the input .vmf, .cfg, and .bsp is valid and uncorrupted')
printConsole('\t* You should always check if the stripper has been implemented correctly in the strippered .vmf')
printConsole('\t* The strippered .vmf can crash hammer via an exception error')
printConsole('\t\tthis does not corrupt the .vmf and you can open it again safely')
printConsole('\t* The script is likely to lose hammer specific settings (e.g. visgroup)')
printConsole('\t\tespecially when modifying and/or deleting by entity model number')
printConsole('\nIf you spot any errors, or have some suggestions you can visit <https://github.com/Source2ZE/Stripplier>')
printConsole('\tor contact <lameskydiver> on discord directly')
printConsole('Thanks!')
printConsole('========================================')

mapname = input('Enter the name of the map\n(make sure all letter cases are the same too!): ')

#create logs
if not os.path.exists('output/'):
    os.makedirs('output/',exist_ok = True)
log = open('output/'+mapname+'_log.txt','w')
error = open('output/'+mapname+'_error_log.txt','w')
errorInit()

printLog("Starting the stripper applier for < "+mapname+" >")
printConsole('\n========================================')
printLog("========================================")

try:
    printConsole("Attempting to read "+mapname+".vmf...")
    readVMF(mapname)
except:
    printConsole("ERROR: Could not find "+mapname+".vmf; make sure a valid vmf with the correct name and letter cases is present!")
    printLog("*** ERROR: "+mapname+".vmf not found ***")
    errorWrite("*** ERROR: "+mapname+".vmf not found ***",'read')
    quitProgram(False)
printLog(mapname+".vmf read")


printConsole('-----')

try:
    printConsole("Attempting to read "+mapname+".bsp...")
    readBSP(mapname)
except:
    printConsole("ERROR: Could not find "+mapname+".bsp; make sure a valid bsp with the correct name and letter cases is present!")
    printLog("*** ERROR: "+mapname+".bsp not found ***")
    errorWrite("*** ERROR: "+mapname+".bsp not found ***",'bsp')
    quitProgram(False)
printLog(mapname+".bsp read")

printConsole('-----')

try:
    printConsole("Attempting to read "+mapname+".cfg...")
    readStripper(mapname)
except:
    printConsole("ERROR: Could not find "+mapname+".cfg; make sure a valid cfg with the correct name and letter cases is present!")
    printLog("*** ERROR: "+mapname+".cfg not found ***")
    errorWrite("*** ERROR: "+mapname+".cfg not found ***",'cfg')
    quitProgram(False)
printLog(mapname+".cfg read")

printLog("========================================")
printConsole("========================================")

stripperApply()

printLog("========================================")
printConsole("========================================")
try:
    printConsole("Attempting to write strippered "+mapname+"_strip.vmf...")
    writeFile(mapname)
except:
    printConsole("ERROR: writing "+mapname+"_strip.vmf; notify the authors of the error with the corresponding log!")
    printLog("*** ERROR: writing "+mapname+"_strip.vmf failed ***")
    errorWrite("*** ERROR: writing "+mapname+"_strip.vmf failed ***",'write')
    quitProgram(False)
printLog(mapname+"_strip.vmf created")
printLog("========================================")

quitProgram(True)