import os, sys, json, subprocess, platform, tempfile, gc
from itertools import chain
pydir = os.path.abspath(os.path.dirname(__file__))
otfccdump = os.path.join(pydir, 'otfcc/otfccdump')
otfccbuild = os.path.join(pydir, 'otfcc/otfccbuild')
if platform.system() in ('Mac', 'Darwin'):
	otfccdump += '1'
	otfccbuild += '1'
if platform.system() == 'Linux':
	otfccdump += '2'
	otfccbuild += '2'
def getmulchar(allch):
	s = str()
	with open(os.path.join(pydir, 'datas/STMulti1.txt'), 'r', encoding = 'utf-8') as f:
		for line in f.readlines():
			litm=line.split('#')[0].strip()
			if not litm: continue
			s += litm
	if not allch: return s
	with open(os.path.join(pydir, 'datas/STMulti2.txt'), 'r', encoding = 'utf-8') as f:
		for line in f.readlines():
			litm=line.split('#')[0].strip()
			if not litm: continue
			s += litm
	return s
def addvariants(font):
	print('Processing font variants...')
	with open(os.path.join(pydir, 'datas/Variants.txt'),'r',encoding = 'utf-8') as f:
		for line in f.readlines():
			litm=line.split('#')[0].strip()
			if '\t' not in litm: continue
			vari=litm.split('\t')
			gtgly=str()
			for ch1 in vari:
				if str(ord(ch1)) in font['cmap']:
					gtgly=font['cmap'][str(ord(ch1))]
					break
			if gtgly:
				for ch1 in vari:
					if str(ord(ch1)) not in font['cmap']:
						font['cmap'][str(ord(ch1))] = gtgly
def removeglyhps(font, sp=False):
	print('Removing glyghs...')
	usedg=set()
	if sp:
		s = set(chain(
			range(0x0000, 0x007F),
			range(0x02B0, 0x0300),
			range(0x2000, 0x2050),
			range(0x2100, 0x2150),
			range(0x3000, 0x301D),
			range(0x3100, 0x3130),
			range(0x31A0, 0x31E3),
			range(0xFE10, 0xFE20),
			range(0xFE30, 0xFE50),
			range(0xFF01, 0xFF66)
		))
		with open(os.path.join(pydir, 'datas/UsedChar.txt'),'r',encoding = 'utf-8') as f:
			for line in f.readlines():
				litm=line.split('#')[0].strip()
				if litm: s.add(ord(litm))
		cdsall=set(map(str, s))
		nmap=set(font['cmap'].keys()).intersection(cdsall)
		usedg.update(set([font['cmap'][mp] for mp in nmap]))
	else:
		usedg.update(set(font['cmap'].values()))
		if 'cmap_uvs' in font:
			for k in font['cmap_uvs'].keys():
				c, v=k.split(' ')
				if c in font['cmap']:
					usedg.add(font['cmap_uvs'][k])
	if 'GSUB' in font:
		for lkn in font['GSUB']['lookupOrder']:
			if lkn in font['GSUB']['lookups']:
				lookup=font['GSUB']['lookups'][lkn]
				if lookup['type'] == 'gsub_single':
					for subtable in lookup['subtables']:
						for g1, g2 in list(subtable.items()):
							if g1 in usedg:
								usedg.add(g2)
				elif lookup['type'] == 'gsub_alternate':
					for subtable in lookup['subtables']:
						for item in set(subtable.keys()):
							if item in usedg:
								usedg.update(set(subtable[item]))
				elif lookup['type'] == 'gsub_ligature':
					for subtable in lookup['subtables']:
						for item in subtable['substitutions']:
							if set(item['from']).issubset(usedg):
								usedg.add(item['to'])
				elif lookup['type'] == 'gsub_chaining':
					for subtable in lookup['subtables']:
						for ls in subtable['match']:
							for l1 in ls:
								usedg.update(set(l1))
	unusegl=set()
	unusegl.update(set(font['glyph_order']))
	notg={'.notdef', '.null', 'nonmarkingreturn', 'NULL', 'NUL'}
	unusegl.difference_update(notg)
	unusegl.difference_update(usedg)
	for ugl in unusegl:
		font['glyph_order'].remove(ugl)
		del font['glyf'][ugl]
	font['cmap']={cod:font['cmap'][cod] for cod in font['cmap'] if font['cmap'][cod] not in unusegl}
	if 'cmap_uvs' in font:
		font['cmap_uvs']={uv:font['cmap_uvs'][uv] for uv in font['cmap_uvs'] if font['cmap_uvs'][uv] not in unusegl}
	if 'GSUB' in font:
		for lookup in font['GSUB']['lookups'].values():
			if lookup['type'] == 'gsub_single':
				for subtable in lookup['subtables']:
					for g1, g2 in list(subtable.items()):
						if g1 in unusegl or g2 in unusegl:
							del subtable[g1]
			elif lookup['type'] == 'gsub_alternate':
				for subtable in lookup['subtables']:
					for item in set(subtable.keys()):
						if item in unusegl or len(set(subtable[item]).intersection(unusegl))>0:
							del subtable[item]
			elif lookup['type'] == 'gsub_ligature':
				for subtable in lookup['subtables']:
					s1=list()
					for item in subtable['substitutions']:
						if item['to'] not in unusegl and len(set(item['from']).intersection(unusegl))<1:
							s1.append(item)
					subtable['substitutions']=s1
			elif lookup['type'] == 'gsub_chaining':
				for subtable in lookup['subtables']:
					for ls in subtable['match']:
						for l1 in ls:
							l1=list(set(l1).difference(unusegl))
	if 'GPOS' in font:
		for lookup in font['GPOS']['lookups'].values():
			if lookup['type'] == 'gpos_single':
				for subtable in lookup['subtables']:
					for item in list(subtable.keys()):
						if item in unusegl:
							del subtable[item]
			elif lookup['type'] == 'gpos_pair':
				for subtable in lookup['subtables']:
					for item in list(subtable['first'].keys()):
						if item in unusegl:
							del subtable['first'][item]
					for item in list(subtable['second'].keys()):
						if item in unusegl:
							del subtable['second'][item]
			elif lookup['type'] == 'gpos_mark_to_base':
				nsb=list()
				for subtable in lookup['subtables']:
					gs=set(subtable['marks'].keys()).union(set(subtable['bases'].keys()))
					if len(gs.intersection(unusegl))<1:
						nsb.append(subtable)
				lookup['subtables']=nsb
def addlookupword(font, stword):
	stword.sort(key=lambda x:len(x[0]), reverse = True)
	subtablesl = list()
	subtablesm = list()
	i, j = 0, 0
	sbs = list()
	sbt = dict()
	wlen = len(stword[0][0])
	while True:
		wds = list()
		wdt = list()
		for s1 in stword[i][0]:
			wds.append(font['cmap'][str(ord(s1))])
		for t1 in stword[i][1]:
			wdt.append(font['cmap'][str(ord(t1))])
		newgname = 'ligast' + str(i)
		font['glyf'][newgname] = {
									'advanceWidth': 0,
									'advanceHeight': 1000,
									'verticalOrigin': 880
								 }
		font['glyph_order'].append(newgname)
		sbs.append({'from': wds, 'to': newgname})
		sbt[newgname] = wdt
		if i >= len(stword) - 1:
			subtablesl.append({'substitutions': sbs})
			subtablesm.append(sbt)
			break
		j += len(stword[i][0] + stword[i][1])
		wlen2 = len(stword[i + 1][0])
		if j >= 20000 or wlen2 < wlen:
			j = 0
			wlen = wlen2
			subtablesl.append({'substitutions': sbs})
			subtablesm.append(sbt)
			sbs = list()
			sbt = dict()
		i += 1
	font['GSUB']['lookups']['wordsc'] = {
											'type': 'gsub_ligature',
											'flags': {},
											'subtables': subtablesl
										}
	font['GSUB']['lookups']['wordtc'] = {
											'type': 'gsub_multiple',
											'flags': {},
											'subtables': subtablesm
										}
def fontaddfont(font, fin2, gb=False):
	print('Loading font2...')
	font2 = json.loads(subprocess.check_output((otfccdump, '--no-bom', fin2)).decode("utf-8", "ignore"))
	if ('CFF_' in font)!=('CFF_' in font2):
		raise RuntimeError('Unable to merge fonts in different formats!')
	if gb:
		print('Adding font2 codes...')
		with open(os.path.join(pydir, 'datas/Variants.txt'),'r',encoding = 'utf-8') as f:
			for line in f.readlines():
				litm=line.split('#')[0].strip()
				if '\t' not in litm: continue
				vari = litm.strip().split('\t')
				gtgly=str()
				for ch1 in vari:
					if str(ord(ch1)) in font2['cmap']:
						gtgly=font2['cmap'][str(ord(ch1))]
						break
				if gtgly:
					for ch1 in vari:
						if str(ord(ch1)) not in font2['cmap']:
							font2['cmap'][str(ord(ch1))] = gtgly
	print('Adding glyphs...')
	f2glcode=dict()
	for codpt, glname in font2['cmap'].items():
		if glname not in f2glcode:
			f2glcode[glname]=list()
		f2glcode[glname].append(codpt)
	scl = 1.0
	if font["head"]["unitsPerEm"] != font2["head"]["unitsPerEm"]:
		scl = font["head"]["unitsPerEm"] / font2["head"]["unitsPerEm"]
	allcd1=set(font['cmap'].keys())
	for f2glyph in font2['glyph_order']:
		if f2glyph not in f2glcode or set(f2glcode[f2glyph]).issubset(allcd1):
			continue
		newnm1 = f2glyph
		j = 1
		while newnm1 in font['glyph_order']:
			newnm1 = f2glyph+'.'+str(j)
			j += 1
		font['glyf'][newnm1] = font2['glyf'][f2glyph]
		if scl != 1.0:
			sclglyph(font['glyf'][newnm1], scl)
		font['glyph_order'].append(newnm1)
		for cdpt in f2glcode[f2glyph]:
			if cdpt not in font['cmap']:
				font['cmap'][cdpt] = newnm1
	del f2glcode
	del font2
	gc.collect()
	if len(font['glyf'])>65535: removeglyhps(font)
	assert len(font['glyf'])<65536, 'The number of glyphs is over 65535.'
def sclglyph(glyph, scl):
	glyph['advanceWidth'] = round(glyph['advanceWidth'] * scl)
	if 'advanceHeight' in glyph:
		glyph['advanceHeight'] = round(glyph['advanceHeight'] * scl)
		glyph['verticalOrigin'] = round(glyph['verticalOrigin'] * scl)
	if 'contours' in glyph:
		for contour in glyph['contours']:
			for point in contour:
				point['x'] = round(point['x'] * scl);
				point['y'] = round(point['y'] * scl);
	if 'references' in glyph:
		for reference in glyph['references']:
			reference['x'] = round(scl * reference['x'])
			reference['y'] = round(scl * reference['y'])
def setnm(font, ennm, tcnm='', scnm='', versn=''):
	print('Processing font name...')
	wt=str()
	for n1 in font['name']:
		if n1['languageID']==1033 and n1['nameID']==2:
			wt=n1['nameString']
		elif n1['languageID']==1033 and n1['nameID']==17:
			wt=n1['nameString']
			break
	if wt.lower() in ('regular', 'bold', 'italic', 'bold italic'):
		wt=wt.title()
	isit='Italic' in wt
	wt=wt.replace('Italic', '').strip()
	if not wt: wt='Regular'
	itml, itm=str(), str()
	if isit: itml, itm=' Italic', 'It'
	if not versn:
		versn=str('{:.2f}'.format(font['head']['fontRevision']))
	else:
		font['head']['fontRevision']=float(versn)
	fmlName=ennm
	ftName=ennm
	ftNamesc=scnm
	ftNametc=tcnm
	if wt not in ('Regular', 'Bold'):
		ftName+=' '+wt
		ftNamesc+=' '+wt
		ftNametc+=' '+wt
	subfamily='Regular'
	if isit:
		if wt=='Bold':
			subfamily='Bold Italic'
		else:
			subfamily='Italic'
	elif wt=='Bold':
		subfamily='Bold'
	psName=fmlName.replace(' ', '')+'-'+wt+itm
	uniqID=versn+';'+psName
	if wt=='Bold':
		fullName=ftName+' '+wt+itml
		fullNamesc=ftNamesc+' '+wt+itml
		fullNametc=ftNametc+' '+wt+itml
	else:
		fullName=ftName+itml
		fullNamesc=ftNamesc+itml
		fullNametc=ftNametc+itml
	newname=list()
	newname+=[
		{'languageID': 1033,'nameID': 1,'nameString': ftName},
		{'languageID': 1033,'nameID': 2,'nameString': subfamily},
		{'languageID': 1033,'nameID': 3,'nameString': uniqID},
		{'languageID': 1033,'nameID': 4,'nameString': fullName},
		{'languageID': 1033,'nameID': 5,'nameString': 'Version '+versn},
		{'languageID': 1033,'nameID': 6,'nameString': psName},
		]
	if wt not in ('Regular', 'Bold'):
		newname+=[
			{'languageID': 1033,'nameID': 16,'nameString': fmlName},
			{'languageID': 1033,'nameID': 17,'nameString': wt+itml}
			]
	if tcnm:
		for lanid in (1028, 3076, 5124):
			newname+=[
				{'languageID': lanid,'nameID': 1,'nameString': ftNametc},
				{'languageID': lanid,'nameID': 2,'nameString': subfamily},
				{'languageID': lanid,'nameID': 4,'nameString': fullNametc}
				]
			if wt not in ('Regular', 'Bold'):
				newname+=[
					{'languageID': lanid,'nameID': 16,'nameString': tcnm},
					{'languageID': lanid,'nameID': 17,'nameString': wt+itml}
					]
	if scnm:
		for lanid in (2052, 4100):
			newname+=[
				{'languageID': lanid,'nameID': 1,'nameString': ftNamesc},
				{'languageID': lanid,'nameID': 2,'nameString': subfamily},
				{'languageID': lanid,'nameID': 4,'nameString': fullNamesc}
				]
			if wt not in ('Regular', 'Bold'):
				newname+=[
					{'languageID': lanid,'nameID': 16,'nameString': scnm},
					{'languageID': lanid,'nameID': 17,'nameString': wt+itml}
					]
	for nl in newname:
		nl['platformID']=3
		nl['encodingID']=1
	font['name']=newname
	if 'CFF_' in font:
		font['CFF_']['fontName']=psName
		font['CFF_']['fullName']=fmlName+' '+wt
		font['CFF_']['familyName']=fmlName
		if 'fdArray' in font['CFF_']:
			nfd=dict()
			for k in font['CFF_']['fdArray'].keys():
				nfd[psName+'-'+k.split('-')[-1]]=font['CFF_']['fdArray'][k]
			font['CFF_']['fdArray']=nfd
			for gl in font['glyf'].values():
				if 'CFF_fdSelect' in gl:
					gl['CFF_fdSelect']=psName+'-'+gl['CFF_fdSelect'].split('-')[-1]
def jptotr(font):
	print('Processing Japanese Kanji...')
	dv = dict()
	if 'cmap_uvs' not in font:
		raise RuntimeError('This font is not applicable!')
	for k in font['cmap_uvs'].keys():
		c, v = k.split(' ')
		if c not in dv:
			dv[c] = dict()
		dv[c][v] = font['cmap_uvs'][k]
	tv = dict()
	with open(os.path.join(pydir, 'datas/uvs-jp-MARK.txt'), 'r', encoding='utf-8') as f:
		for line in f.readlines():
			litm=line.split('#')[0].strip()
			if litm.endswith('X'):
				a = litm.split(' ')
				tv[str(ord(a[0]))] = str(int(a[3].strip('X'), 16))
	for k in dv.keys():
		if k in tv:
			if tv[k] in dv[k]:
				tch = dv[k][tv[k]]
				font['cmap'][k] = tch
def mapts(font, chardic, ignch):
	for ch in chardic.keys():
		if ch in ignch: continue
		cdto=str(ord(chardic[ch]))
		if cdto in font['cmap']:
			font['cmap'][str(ord(ch))] = font['cmap'][cdto]
def checklk(font):
	if not 'GSUB' in font:
		font['GSUB'] = {
			'languages': {},
			'features': {},
			'lookups': {},
			'lookupOrder': []
		}
	for scrtg in ['DFLT_DFLT', 'hani_DFLT', 'latn_DFLT']:
		if scrtg not in font['GSUB']['languages']:
			font['GSUB']['languages'][scrtg] = {'features': []}
	for table in font['GSUB']['languages'].values():
		table['features'].insert(0, 'ccmp_st')
	font['GSUB']['features']['ccmp_st'] = ['wordsc', 'stchars', 'wordtc']
	font['GSUB']['lookupOrder']=['wordsc', 'stchars', 'wordtc']+font['GSUB']['lookupOrder']
def linesplit(l, ch):
	litm=l.split('#')[0].strip().split(' ')[0]
	if ch not in litm: return '', ''
	lnst=litm.split(ch)
	return lnst[0].strip(), lnst[1].strip()
def getdictxt(tabnm):
	txtdic=dict()
	with open(os.path.join(pydir, f'datas/{tabnm}.txt'),'r',encoding = 'utf-8') as f:
		for line in f.readlines():
			s, t=linesplit(line, '\t')
			if s and t and s != t:
				txtdic[s]=t
	return txtdic
def varck(text, vardic):
	for ch in vardic.keys():
		text=text.replace(ch, vardic[ch])
	return text
def stts(font, wkon, vr=False):
	tabset=wkon.split('.')
	tabch=tabset[0]
	chardic, vardic, wddic=dict(), dict(), dict()
	mulp, locset, mulchar=str(), str(), str()
	if tabch=='st':
		locset, mulp=tabset[1], tabset[2]
		if mulp!='s':
			mulchar = getmulchar(mulp == "m")
		if mulp=='m' and locset in ['tw', 'twp'] and '么' not in mulchar:
			mulchar+='么'
	chardic=getdictxt('Chars_'+tabch)
	if locset in ['tw', 'hk', 'cl', 'twp']:
		if locset=='twp':vardic=getdictxt('Var_tw')
		else: vardic=getdictxt('Var_'+locset)
		for ch in vardic.keys():
			if ch not in chardic.values():
				chardic[ch]=vardic[ch]
		for ch in list(chardic.keys()):
			if chardic[ch] in vardic:
				chardic[ch]=vardic[chardic[ch]]
	if tabch == 'ts' or mulp == "m":
		phrases=f'datas/{tabch.upper()}Phrases.txt'
		with open(os.path.join(pydir, phrases),'r',encoding = 'utf-8') as f:
			for line in f.readlines():
				s, t=linesplit(line, '\t')
				if not(s and t): continue
				if locset in ['tw', 'hk', 'cl', 'twp']:
					t=varck(t, vardic)
				wddic[s]=t
		if locset=='twp':
			with open(os.path.join(pydir, 'datas/TWPhrases.txt'),'r',encoding = 'utf-8') as f:
				for line in f.readlines():
					s, t=linesplit(line, '\t')
					if not(s and t): continue
					if len(s)==1 and len(t)==1:
						chardic[s]=t
					else:
						wddic[s]=t
	mapts(font, chardic, mulchar)
	if mulp == "m":
		removeglyhps(font, True)
		if vr: addvariants(font)
	else:
		removeglyhps(font, False)
	if tabch == 'ts' or mulp == "m":
		print('Check font lookups...')
		checklk(font)
		if tabch=='ts':
			ftdic=getdictxt('Chars_tsm')
		else:
			ftdic=dict()
			for ch in chardic.keys():
				if ch in mulchar:
					ftdic[ch]=chardic[ch]
			if locset in ['tw', 'twp']:
				ftdic['么']='麼'
				ftdic['幺']='么'
		kt=dict()
		for ch in ftdic.keys():
			cd1, cd2=str(ord(ch)), str(ord(ftdic[ch]))
			if cd1 in font['cmap'] and cd2 in font['cmap'] and font['cmap'][cd1]!=font['cmap'][cd2]:
				kt[font['cmap'][cd1]]=font['cmap'][cd2]
		font['GSUB']['lookups']['stchars'] = {'type': 'gsub_single', 'flags': {}, 'subtables': [kt]}
		stword = list()
		ccods=set(font['cmap'].keys())
		for wd in wddic.keys():
			s, t=wd, wddic[wd]
			codestc = set(str(ord(c)) for c in s+t)
			if codestc.issubset(ccods):
				stword.append((s, t))
		if len(stword) + len(font['glyph_order']) > 65535:
			nd=len(stword) + len(font['glyph_order']) - 65535
			raise RuntimeError('Not enough glyph space! You need ' + str(nd) + ' more glyph space!')
		if len(stword) > 0:
			addlookupword(font, stword)
def parseArgs(args):
	nwk=dict()
	nwk['inFilePath'], nwk['outFilePath'], nwk['outFilePath2'], nwk['enN'], nwk['scN'], nwk['tcN'], nwk['vsN']=(str() for i in range(7))
	nwk['varit'], nwk['toST'], nwk['toTS'], nwk['jpCL'], nwk['rmUN']=(False for i in range(5))
	argn = len(args)
	i = 0
	while i < argn:
		arg  = args[i]
		i += 1
		if arg == "-o":
			nwk['outFilePath'] = args[i]
			i += 1
		elif arg == "-i":
			nwk['inFilePath'] = args[i]
			i += 1
		elif arg == "-i2":
			nwk['inFilePath2'] = args[i]
			i += 1
		elif arg == "-wk":
			nwk['work'] = args[i]
			i += 1
		elif arg == "-v":
			nwk['varit'] = True
		elif arg == "-n":
			nwk['enN'] = args[i]
			i += 1
		elif arg == "-nsc":
			nwk['scN'] = args[i]
			i += 1
		elif arg == "-ntc":
			nwk['tcN'] = args[i]
			i += 1
		elif arg == "-vn":
			nwk['vsN'] = args[i]
			i += 1
		else:
			raise RuntimeError("Unknown option '%s'." % (arg))
	if not nwk['inFilePath']:
		raise RuntimeError("You must specify one input font.")
	if not nwk['outFilePath']:
		raise RuntimeError("You must specify one output font.")
	if nwk['work'] in ("sat", "faf") and not nwk['inFilePath2']:
		raise RuntimeError("You must specify one input font2.")
	if not nwk['enN'] and (nwk['tcN'] or nwk['scN'] or nwk['vsN']):
		raise RuntimeError("You must specify English name first.")
	return nwk
def run(args):
	print('Loading font...')
	wkfl=parseArgs(args)
	infont=json.loads(subprocess.check_output((otfccdump, '--no-bom', wkfl['inFilePath'])).decode("utf-8", "ignore"))
	if wkfl['work'] in ("sat", "faf"):
		fontaddfont(infont, wkfl['inFilePath2'], wkfl['work']=="sat")
	if wkfl['work']=='jt':
		jptotr(infont)
	if wkfl['work']=="var" or wkfl['varit']:
		addvariants(infont)
	if wkfl['work'].split('.')[0] in ("st", "ts"):
		stts(infont, wkfl['work'], wkfl['varit'])
	if wkfl['enN']:
		setnm(infont, wkfl['enN'], wkfl['tcN'], wkfl['scN'], wkfl['vsN'])
	print('Saving font...')
	tmpfile = tempfile.mktemp('.json')
	with open(tmpfile, 'w', encoding='utf-8') as f:
		f.write(json.dumps(infont))
	del infont
	gc.collect()
	subprocess.run((otfccbuild, '--keep-modified-time', '--keep-average-char-width', '-O3', '-q', '-o', wkfl['outFilePath'], tmpfile))
	os.remove(tmpfile)
	print('Finished!')
def main():
	run(sys.argv[1:])
if __name__ == "__main__":
	main()
