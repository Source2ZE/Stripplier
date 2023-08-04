import re
import os

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

def quitProgram(successful):
    print('========================================')
    if successful:
        printConsole('The program has ended successfully; press enter to exit')
        printLog("End.")
        log.close()
        input()
    else:
        printConsole('The program has ended unsuccessfully; press enter to exit')
        printLog("Unsuccessful end.")
        log.close()
        input()
        assert False

def printConsole(text):
    print(text+'\n')

def printLog(text):
    log.write(text+'\n')

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
            v = row[idx+1:row.find('"',idx+1)]
        count += 1
        idx = row.find('"',idx+1)
    return k, v

#prevent a dict from overriding other existing dict of same key
def returnUniqueName(parent,name):
    count = 0
    unique = name
    while(unique in parent):
        unique = name + str(count)
        count += 1
    return unique

def appendTab(string,amount):
    return '\t'*amount + string

def writeDictKV(k,v):
    return '"'+k+'" "'+v+'"\n'

#writes each block in vmf
def writeScope(file, dic, gen):
    if not dic:
        file.write(appendTab('}',gen))
    for row in dic:
        #print(row, type(dic[row])==dict,len(dic[row]))
        if row == '_':
            continue
        if type(dic[row])==dict:
            #dictionary has more keyvalues other than its name and a dummy kv
            if len(dic[row])>2:
                file.write(appendTab(dic[row]['k']+"\n",gen))
                file.write(appendTab("{\n",gen))
                writeScope(file, dic[row], gen+1)
                file.write(appendTab("}\n",gen))
            else:
                writeScope(file, dic[row], gen)
        elif row!='k':
            file.write(appendTab(writeDictKV(row,dic[row]),gen))
    return file

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
    if dic['k'] == 'cordons':
        cordons.append(dic)

def readFile(name):
    with open('input/'+name+'.vmf', 'r') as file:
        dic = None
        parent = []
        gen = 0#tracks generations of scopes
        for row in file:
            #row = file.readline()
            row = row.strip()
            #if not row:
            #    break
            if row == '{':
                gen += 1
            elif row == '}':
                gen -= 1
                if(gen > 0):
                    parent[-1][returnUniqueName(parent[-1],dic['k'])] = dic
                    dic = parent.pop()
                else:
                    appendDict(dic)
                    dic = None
            #this will be the name of a subscope (e.g. connections:)
            elif row.find('"')==-1:
                if gen > 0:
                    parent.append(dic)
                dic = {'k': row}
                dic['_'] = ' '
            else:
                k,v = findKV(row)
                unique = returnUniqueName(dic,k)
                dic[unique] = {'k':k}
                dic[unique][k] = v

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

stripper = []
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
                elif row.find(':')!=-1 and row.find('"')==-1:
                    if gen > 0:
                        parent.append(dic)
                    dic = {'k': row}
                else:
                    k,v = findKV(row)
                    #fix small quirk between vmf and stripper formatting
                    if k == 'hammerid':
                        k = 'id'
                    if v.find('') == -1 and v.find(',') == -1:
                        0
                    else:
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

bsp = []
def readBSP(name):
    with open('input/'+name+'.bsp','r',errors='ignore') as file:
        for row in file:
            row = row.strip()
            #skip any gibberish and empty newlines
            if len(row)>0 and (row[0]=='"' or row[0]=='{' or row[0]=='}'):
                bsp.append(row)

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
        try:
            printLog('\t  "'+k+'" "'+ent[k][k]+'"')
        except:
            0

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
def vecDist(vec1,vec2):
    return {'x':vec2['x']-vec1['x'],'y':vec2['y']-vec1['y'],'z':vec2['z']-vec1['z']}

#isint = True if the output has to be in integer format
def vecAdd(vec1,vec2,isint):
    temp = {'x':vec2['x']+vec1['x'],'y':vec2['y']+vec1['y'],'z':vec2['z']+vec1['z']}
    if(isint):
        temp['x'] = int(temp['x'])
        temp['y'] = int(temp['y'])
        temp['z'] = int(temp['z'])
    return temp

#shift plane [which has format of '(x1 y1 z1) (x2 y2 z2) (x3 y3 z3)'] by a specified vector
def shiftPlane(plane, dist):
    bra = plane.find('(')
    ket = plane.find(')')
    new = ''
    while True:
        new += '('
        new += vecToStr(vecAdd(strToVec(plane[bra+1:ket]),dist,True))
        new += ')'
        bra = plane.find('(',bra+1)
        if bra < 0:
            break
        ket = plane.find(')',ket+1)
        new += ' '
    return new

#change kv inside editor block to let know the ent is from a stripper fix
def stripperEditor(editor):
    editor = {key: val for key, val in editor.items() if key == 'k' or key == '_'}
    editor['color'] = {'k':'color','color':'0 0 255'}
    editor['comments'] = {'k':'comments','comments':'Stripper fixed'}
    editor['k'] = 'editor'
    editor['_'] = ''
    return editor

#find ent by model number
def findEntFunc(model):
    idx = bsp.index('"model" "'+model+'"')+1
    hammerid = None
    origin = None
    #only search until hammerid and origin is found - this is enough to find the corresponding ent in .vmf
    while not hammerid or not origin:
        #print(bsp[idx])
        if bsp[idx].find('hammerid') != -1:
            hammerid = bsp[idx][12:bsp[idx].find('"',13)]
        if bsp[idx].find('origin') != -1:
            origin = bsp[idx][10:bsp[idx].find('"',11)]
        idx += 1
    for e in ents:
        try:
            if e['id']['id'] == hammerid and e['origin']['origin'] == origin:
                return e
        except:
            0
    return None

#duplicate side of a solid
def duplicateSolidSide(side):
    dupe = {}
    for k in side:
        if k != 'id':
            if k == '_':
                dupe[k] = ''
            elif k == 'k':
                dupe[k] = 'side'
            elif len(side[k]) <= 2:
                dupe[k] = {'k':side[k]['k'],side[k]['k']:side[k][side[k]['k']]}
            else:
                dupe[k] = {'k':'vertices_plus','_':''}
                for v in side[k]:
                    if v != 'k' and v != '_':
                        dupe[k][v] = {'k':side[k][v]['k'],side[k][v]['k']:side[k][v][side[k][v]['k']]}
    return dupe

#duplicate the geometry of a given ent to a new origin
def duplicateEntFunc(ent, new_origin):
    dist = vecDist(strToVec(ent['origin']['origin']),strToVec(new_origin))
    new = {'solid':{'k':'solid','_':''}}
    new['editor'] = stripperEditor({})
    for row in ent['solid']:
        if row == '_':
            new['solid'][row] = ''
        elif row == 'editor':
            new['solid'][row] = stripperEditor({})
        elif row == 'k':
            new['solid']['k'] = 'solid'
        elif row == 'id':
            continue
        #create 6 sides of the solid
        else:
            new['solid'][row] = duplicateSolidSide(ent['solid'][row])
            new['solid'][row]['plane'] = {'k':'plane','plane':shiftPlane(ent['solid'][row]['plane']['plane'],dist)}
            for v in new['solid'][row]['vertices_plus']:
                if v != 'k' and v != '_':
                    new['solid'][row]['vertices_plus'][v]['v'] = vecToStr(vecAdd(strToVec(new['solid'][row]['vertices_plus'][v]['v']),dist,True))
    new['strippered'] = {'k':'strippered','strippered':'1'}
    return new

#create a default side of a solid
#assumed created func is likely to be a trigger
def createSolidSide():
    return {'k':'side','_':'','material':{'k':'material','material':'TOOLS/TOOLSTRIGGER'},'rotation':{'k':'rotation','rotation':'0'},'lightmapscale':{'k':'lightmapscale','lightmapscale':'16'},'smoothing_groups':{'k':'smoothing_groups','smoothing_groups':'0'}}

#try to find if there is logic_auto/logic_relay/whatever else that defines boundary size of the new trigger/func brush
def findSolidBoundary(ent_name, ent_origin):
    mins = None
    maxs = None
    target = []
    for s in stripper:
        if mins and maxs:
            break
        #try to look at the same stripper block first
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
        try:
            del_idx = []
            #stripper is of modify: type
            for i in s['insert:']:
                if mins and maxs:
                    break
                if i != 'k' and s['insert:'][i][s['insert:'][i]['k']].find(ent_name) == 0:
                    #print(s['insert:'][i][s['insert:'][i]['k']])
                    if s['insert:'][i][s['insert:'][i]['k']].find('mins') != -1:
                        mins = strToVec(findCoordFromInsert(s['insert:'][i][s['insert:'][i]['k']][s['insert:'][i][s['insert:'][i]['k']].find('mins')+5:]))
                        #print('test')
                        del_idx.append(i)
                        if s not in target:
                            target.append(s)
                    if s['insert:'][i][s['insert:'][i]['k']].find('maxs') != -1:
                        maxs = strToVec(findCoordFromInsert(s['insert:'][i][s['insert:'][i]['k']][s['insert:'][i][s['insert:'][i]['k']].find('maxs')+5:]))
                        #print('test')
                        del_idx.append(i)
                        if s not in target:
                            target.append(s)
            for d in del_idx:
                del s['insert:'][d]
        except:
            #stripper is of add: type
            try:
                del_idx = []
                for i in s:
                    if mins and maxs:
                        break
                    if i != 'k' and i != 'add:' and s[i][s[i]['k']].find(ent_name) == 0:
                        if s[i][s[i]['k']].find('mins') != -1:
                            mins = strToVec(findCoordFromInsert(s[i][s[i]['k']][s[i][s[i]['k']].find('mins')+5:]))
                            del_idx.append(i)
                            if s not in target:
                                target.append(s)
                        if s[i][s[i]['k']].find('maxs') != -1:
                            maxs = strToVec(findCoordFromInsert(s[i][s[i]['k']][s[i][s[i]['k']].find('maxs')+5:]))
                            del_idx.append(i)
                            if s not in target:
                                target.append(s)
                for d in del_idx:
                    del s[d]
            except:
                0
    #if all fails then assign default volume of +-100 to each dimension
    if not mins or not maxs:
        mins = vecAdd(strToVec(ent_origin),{'x':-100,'y':-100,'z':-100},True)
        maxs = vecAdd(strToVec(ent_origin),{'x':100,'y':100,'z':100},True)
    #if mins/maxs was found apply it to newly created func's origin
    else:
        mins = vecAdd(strToVec(ent_origin),mins,True)
        maxs = vecAdd(strToVec(ent_origin),maxs,True)
    return mins, maxs, target

#create a solid for a brush
def createSolid(ent):
    mins = None
    maxs = None
    target = None
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
    solid = {'k':'solid','_':'','editor':stripperEditor({})}
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

def isNumericOrWS(char):
    if ord(char) == 45 or ord(char) == 46 or ord(char) == 32 or (ord(char)>=48 and ord(char)<=57):
        return True
    else:
        return False

#try to find coordinates from an insert: line
#to be used to find mins/maxs boundary of new func ent
def findCoordFromInsert(partial):
    coord = ''
    for c in partial:
        if isNumericOrWS(c):
            coord += c
        else:
            return coord

#assume all regex starts and end with '/'
def isRegex(value):
    if value[0] == '/' and value[-1] == '/':
        return True
    else:
        return False

#perform insert:
def stripperInsert(ent, insert, i):
    #normal kv
    if insert[i][insert[i]['k']].find('') == -1 and insert[i][insert[i]['k']].find(',') == -1:
        ent[i] = {'k':insert[i]['k'],insert[i]['k']:insert[i][insert[i]['k']]}
    #connection kv
    else:
        #ent may not already have 'connections' dict created
        try:
            ent['connections']
        except:
            ent['connections'] = {'k':'connections','_':''}
        ent['connections'][returnUniqueName(ent['connections'],insert[i]['k'])] = {'k':insert[i]['k'],insert[i]['k']:insert[i][insert[i]['k']]}
        #print(ent['connections'])
    return ent

#perform modify:
def stripperStrip(ent,insert,replace,delete):
    #perform delete:
    if delete:
        for d in delete:
            if d != 'k':
                try:
                    #regex
                    if isRegex(delete[d][delete[d]['k']]):
                        del_idx = []
                        for t in ent['connections']:
                            if t != 'k' and t != '_':
                                if re.search(delete[d][delete[d]['k']][1:-1],ent['connections'][t][ent['connections'][t]['k']]):
                                    del_idx.append(t)
                        for d in del_idx:
                            del ent['connections'][d]
                    #normal kv
                    elif delete[d][delete[d]['k']].find('') == -1 and delete[d][delete[d]['k']].find(',') == -1:
                        del ent[d]
                    #connections kv
                    else:
                        for t in ent['connections']:
                            if t != 'k' and t != '_':
                                if re.sub(r'[,]+','',ent['connections'][t][ent['connections'][t]['k']]) == re.sub(r'[,]+','',delete[d][delete[d]['k']]):
                                    del ent['connections'][t]
                                    break
                except:
                    printLog('\n*** WARNING: Attempting to delete an invalid keyvalue pair [ "'+delete[d]['k']+'" "'+delete[d][delete[d]['k']]+'" ] - is this intentional? ***\n')
    if insert:
        for i in insert:
            if i != 'k':
                stripperInsert(ent,insert,i)
    if replace:
        for r in replace:
            if r != 'k':
                try:
                    ent[r][ent[r]['k']] = replace[r][replace[r]['k']]
                #some kv with default values (e.g. spawnflag 0) may not be defined in .vmf - perform insert: in this case
                except:
                    printLog('\n*** WARNING: The keyvalue pair [ "'+replace[r]['k']+'" "'+replace[r][replace[r]['k']]+'" ] could not be replaced - attempting to insert instead ***\n')
                    stripperInsert(ent,replace,r)
    ent['editor'] = stripperEditor(ent['editor'])
    ent['strippered'] = {'k':'strippered','strippered':'1'}

#find ents matching with match: and perform modify: on targetted ents
def stripperModify(strip):
    count = 1
    printLog('\nThis will modify the following entity/entities:')
    for idx in range(len(ents)):
        skip = True
        for m in strip['match:']:
            #small quirk between vmf and stripper formats
            if m == 'hammerid':
                m = 'id'
            if m == 'k':
                continue
            try:
                #value is regex format
                if isRegex(strip['match:'][m][strip['match:'][m]['k']]):
                    #search for normal kv first
                    try:
                        #not the ent we're looking for
                        if not re.search(strip['match:'][m][strip['match:'][m]['k']][1:-1],ents[idx][m][ents[idx][m]['k']]):
                            skip = True
                            break
                        else:
                            skip = False
                    #then search for connection kv
                    except:
                        try:
                            for c in ents[idx]['connections']:
                                if c != 'k' and c!= '_':
                                    #the targetted ent has the kv we want
                                    if re.search(strip['match:'][m][strip['match:'][m]['k']][1:-1],ents[idx]['connections'][c][ents[idx]['connections'][c]['k']]):
                                        skip = False
                                        break
                        except:
                            skip = True
                else:
                    #normal kv
                    if strip['match:'][m][strip['match:'][m]['k']].find('') == -1 and strip['match:'][m][strip['match:'][m]['k']].find(',') == -1:
                        #not the target ent
                        if strip['match:'][m][strip['match:'][m]['k']].lower() != ents[idx][m][ents[idx][m]['k']].lower():
                            skip = True
                            break
                        else:
                            #print(ents[idx][m][ents[idx][m]['k']])
                            #print(strip['match:'][m],'bbb')
                            skip = False
                   #connection kv
                    else:
                        #not the target ent
                        if strip['match:'][m][strip['match:'][m]['k']] not in [ents[idx]['connections'][x][ents[idx]['connections'][x]['k']] for x in ents[idx]['connections'] if x != 'k' and x != '_']:
                            skip = True
                            break
                        else:
                            skip = False
            except:
                skip = True
                break
        #we found the target ent
        if not skip:
            printLog('\tEntity '+str(count)+':')
            printEntityInfo(ents[idx])
            insert = None
            replace = None
            delete = None
            for b in strip:
                if b != 'k' and b != 'match:':
                    if b == 'insert:':
                        insert = strip[b]
                    elif b == 'replace:':
                        replace = strip[b]
                    elif b == 'delete:':
                        delete = strip[b]
            #strip the ent
            stripperStrip(ents[idx], insert, replace, delete)
            count += 1
    #no ents were stripped
    if count == 1:
        printLog('\t*** WARNING: No valid entity has been targetted! ***')
    printStripperModifications(strip)

added_ents = []#track ents that were added - tracked for any new func ents that may have boundaries defined later

#perform add:
def stripperAdd(strip):
    ent = {}
    dupe = False
    try:
        #assume add: with model number is duplication of existing brush
        if strip['model']['model'].find('*')!=-1:
            dupe = True
    except:
        dupe = False
    connections = {'k':'connections','_':''}
    #need to create fresh ent
    if not dupe:
        #add kv
        for k in strip:
            if k != 'k':
                #normal kv
                if strip[k][strip[k]['k']].find('') == -1 and strip[k][strip[k]['k']].find(',') == -1:
                    ent[k] = {'k':strip[k]['k'], strip[k]['k']:strip[k][strip[k]['k']]}
                #connection kv
                else:
                    connections[k] = {'k':strip[k]['k'], strip[k]['k']:strip[k][strip[k]['k']]}
        ent['editor'] = stripperEditor({})
        ent['connections'] = connections
        #if it is a trigger_ or func_, a 3d brush is also necessary
        if ent['classname']['classname'].find('trigger_') == 0 or ent['classname']['classname'].find('func_') == 0:
            ent['solid'] = createSolid(ent)
    #need to duplicate from an existing ent
    else:
        printLog('\nThis entity will copy the solid(/brush) of the following entity:')
        target = findEntFunc(strip['model']['model'])
        #model number does not exist in bsp
        if not target:
            printLog('\n*** ERROR: a solid(/brush) with model number "'+strip['model']['model']+'has not been found ***')
        printEntityInfo(target)
        #duplicate info about brush solid
        ent = duplicateEntFunc(target,strip['origin']['origin'])
        #add kv
        for k in strip:
            if k != 'k' and k != 'model':
                #normal kv
                if strip[k][strip[k]['k']].find('') == -1 and strip[k][strip[k]['k']].find(',') == -1:
                    ent[k] = {'k':strip[k]['k'], strip[k]['k']:strip[k][strip[k]['k']]}
                #connection kv
                else:
                    connections[k] = {'k':strip[k]['k'], strip[k]['k']:strip[k][strip[k]['k']]}
        #append connection dict if a/multiple connection kv exist(s)
        if len(connections) > 2:
            ent['connections'] = connections
    ent['k'] = 'entity'
    ent['_'] = ''
    ent['strippered'] = {'k':'strippered','strippered':'1'}
    ents.append(ent)
    added_ents.append(ent)

#perform filter:
def stripperFilter(strip):
    printLog('\nThis will delete the following entity/entities:')
    del_ent = []
    for idx in range(len(ents)):
        skip = True
        #try to find targeting ents defined in filter: stripper block
        for m in strip:
            if m == 'k':
                continue
            try:
                if isRegex(strip[m][m]):
                    #not the targetted ent
                    if not re.search(strip[m][m][1:-1].lower(),ents[idx][m][m].lower()):
                        skip = True
                        break
                    else:
                        skip = False
                else:
                    #not the t argetted ent
                    if strip[m][m].lower() != ents[idx][m][m].lower():
                        skip = True
                        break
                    else:
                        skip = False
            except:
                skip = True
                break
        #we found the targetted ent
        if not skip:
            del_ent.append(idx)
    #go through all ents to be deleted, print their info and delete them
    for idx, d in enumerate(del_ent[::-1]):
        printLog('\tEntity '+str(idx+1)+':')
        printEntityInfo(ents[d])
        del ents[d]

#perform actions of each stripper block
def stripperApply():
    count = 1
    for strip in stripper:
        printLog('-+ Stripper Block #'+str(count)+' +-')
        printConsole('-+ Working stripper block #'+str(count)+' +-')
        printStripperMatch(strip)
        try:
        #log.write(strip['k'])
        #log.write("------------")
            if strip['k']=='modify:':
                stripperModify(strip)
            elif strip['k']=='add:':
                stripperAdd(strip)
            elif strip['k']=='filter:':
                stripperFilter(strip)
        except:
            printConsole('ERROR: stripper block could not be applied - skipping')
            printLog("ERROR: stripper block could not be applied - skipping")
        printLog('\n')
        count += 1

printConsole('Stripplier v1.1')
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
printConsole('\nIf you spot any errors, or have some suggestions you can visit <https://github.com/Source2ZE/Stripplier>')
printConsole('\tor contact <lameskydiver> on discord directly')
printConsole('Thanks!')
printConsole('========================================')

mapname = input('Enter the name of the map\n(make sure all letter cases are the same too!): ')

if not os.path.exists('output/'):
    os.makedirs('output/',exist_ok = True)
log = open('output/'+mapname+'_logs.txt','w')

printLog("Starting the stripper applier for < "+mapname+" >")
printConsole('\n========================================')
printLog("========================================")

try:
    printConsole("Attempting to read "+mapname+".vmf...")
    readFile(mapname)
except:
    printConsole("ERROR: Could not find "+mapname+".vmf; make sure a valid vmf with the correct name and letter cases is present!")
    printLog("ERROR: "+mapname+".vmf not found")
    quitProgram(False)
printLog(mapname+".vmf found")

printConsole('-----')
try:
    printConsole("Attempting to read "+mapname+".bsp...")
    readBSP(mapname)
except:
    printConsole("ERROR: Could not find "+mapname+".bsp; make sure a valid bsp with the correct name and letter cases is present!")
    printLog("ERROR: "+mapname+".bsp not found")
    quitProgram(False)
printLog(mapname+".bsp found")

printConsole('-----')
try:
    printConsole("Attempting to read "+mapname+".cfg...")
    readStripper(mapname)
except:
    printConsole("ERROR: Could not find "+mapname+".cfg; make sure a valid cfg with the correct name and letter cases is present!")
    printLog("ERROR: "+mapname+".cfg not found")
    quitProgram(False)
printLog(mapname+".cfg found")

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
    printLog("ERROR: writing "+mapname+"_strip.vmf failed")
    quitProgram(False)
printLog(mapname+"_strip.vmf created")
printLog("========================================")

quitProgram(True)