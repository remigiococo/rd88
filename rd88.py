from sys import version_info
if version_info.major == 2:
	# Python 2.x
	import Tkinter as tk
	from Tkinter import ttk
	import tkFileDialog as filedialog
	from cStringIO import StringIO
elif version_info.major == 3:
	# Python 3.x
	import tkinter as tk
	from tkinter import ttk
	from tkinter import filedialog
	from io import StringIO as StringIO

from sysex1 import *
from win32midi import Win32MidiIO
from rd88lists import *
from rd88mfx import *
import pickle

class SceneData():
	def __init__(self):
		self.nzones = 3
		self.nparams = len(ToneParams)
		self.tone_params = [ [ 0 for j in range(self.nparams) ] for i in range(self.nzones) ]
		self.cur_category = [ 0 for i in range(self.nzones) ]
		self.cur_sound = [ 0 for i in range(self.nzones) ]
		self.enabled = [ 1, 0, 0 ]
		
class Rd88Editor(tk.Frame):
	def __init__(self,master=None,w=800,h=600):
		tk.Frame.__init__(self, master,width=w, height=h)
		self.rowconfigure(0, weight=1)
		self.columnconfigure(0, weight=1)
		#self.grid(sticky="NSEW")
		self.pack(expand=True, fill=tk.BOTH)
		self.update()
		self.createWidgets()
		self.sd = SceneData()
		self.initData()
		
	def createWidgets(self):
		self.nb = ttk.Notebook(self, width=self.winfo_width(), height=self.winfo_height())
		self.nb.rowconfigure(0, weight=1)
		self.nb.columnconfigure(0, weight=1)
		self.nb.grid(row=0, column=0, sticky="NSEW")
		######
		self.tabs = ["MIDI", "Scenes", "Tones", "MFX"]
		self.n_tabs = len(self.tabs)
		self.tab = []
		for i in range(self.n_tabs):
			self.tab.insert( i, tk.Frame(self.nb) )
		######
		# inizializzazione specifica per tab
		cur_tab = self.tabs.index("MIDI")
		self.tab[cur_tab].rowconfigure(0, weight=1)
		self.tab[cur_tab].rowconfigure(1, weight=20)
		self.tab[cur_tab].columnconfigure(0, weight=1)
		self.tab[cur_tab].grid(sticky="NSEW")
		self.w = dict()
		self.w["midiport"] = ttk.Combobox(self.tab[cur_tab], state=['readonly'])
		self.w["curport"] = tk.Text(self.tab[cur_tab])
		self.w["midiport"].bind("<<ComboboxSelected>>", self.onMidiPort)
		self.w["midiport"].grid(sticky="NSEW")
		self.w["curport"].grid(sticky="NSEW")
		#------
		cur_tab = self.tabs.index("Scenes")
		self.tab[cur_tab].rowconfigure(0, weight=1)
		self.tab[cur_tab].rowconfigure(1, weight=1)
		self.tab[cur_tab].rowconfigure(2, weight=1)
		self.tab[cur_tab].rowconfigure(3, weight=20)
		self.tab[cur_tab].columnconfigure(0, weight=1)
		self.tab[cur_tab].columnconfigure(1, weight=1)
		self.tab[cur_tab].grid(sticky="NSEW")
		self.w["scenenum"] = ttk.Entry(self.tab[cur_tab])
		self.w["scenenum"].grid(row=0, column=0, sticky="NS")
		self.w["scenechg"] = tk.Button(self.tab[cur_tab], text="Change Scene")
		self.w["scenechg"].grid(row=0, column=1, sticky="NS")
		self.w["scenechg"].configure(command=self.onChangeScene)
		self.w["opendata"] = tk.Button(self.tab[cur_tab], text="Open")
		self.w["opendata"].grid(row=1, column=0, sticky="NS")
		self.w["opendata"].configure(command=self.onOpen)
		self.w["savedata"] = tk.Button(self.tab[cur_tab], text="Save")
		self.w["savedata"].grid(row=1, column=1, sticky="NS")
		self.w["savedata"].configure(command=self.onSave)
		self.w["nomefile"] = tk.Label(self.tab[cur_tab], text="---")
		self.w["nomefile"].grid(row=2, columnspan=2, sticky="NS")
		#------
		cur_tab = self.tabs.index("Tones")
		npar = len(ToneParams)
		self.tab[cur_tab].rowconfigure(0, weight=1)
		self.tab[cur_tab].rowconfigure(1, weight=1)
		self.tab[cur_tab].rowconfigure(2, weight=1)
		self.tab[cur_tab].rowconfigure(3, weight=1)
		for i in range(npar):
			self.tab[cur_tab].rowconfigure(4+i, weight=1)
		self.tab[cur_tab].columnconfigure(0, weight=1)
		self.tab[cur_tab].columnconfigure(1, weight=1)
		self.tab[cur_tab].grid(sticky="NSEW")
		self.w["category_l"] = tk.Label(self.tab[cur_tab], text="Category")
		self.w["category_l"].grid(row=1,column=0, sticky="NS")
		self.w["tone_l"] = tk.Label(self.tab[cur_tab], text="Tone")
		self.w["tone_l"].grid(row=1,column=1, sticky="NS")
		self.w["category"] = ttk.Combobox(self.tab[cur_tab], state=['readonly'])
		self.w["category"].grid(row=0, column=0, sticky="NS")
		self.w["category"].bind("<<ComboboxSelected>>", self.onCategory)
		self.w["tone"] = ttk.Combobox(self.tab[cur_tab], state=['readonly'])
		self.w["tone"].grid(row=0, column=1, sticky="NS")
		self.w["tone"].bind("<<ComboboxSelected>>", self.onTone)
		self.w["zone"] = ttk.Combobox(self.tab[cur_tab], state=['readonly'])
		self.w["zone"].grid(row=2, column=0, sticky="NSWE")
		self.w["zone"].bind("<<ComboboxSelected>>", self.onZone)
		self.w["zone_l"] = tk.Label(self.tab[cur_tab], text="Current Zone", background='yellow')
		self.w["zone_l"].grid(row=2, column=1, sticky="WNS")
		self.Upper1 = tk.IntVar()
		self.Upper2 = tk.IntVar()
		self.Lower = tk.IntVar()
		self.Upper1.set(1) 
		self.Upper2.set(0) 
		self.Lower.set(0)
		self.w["en_up1"] = ttk.Checkbutton(self.tab[cur_tab], text="Enable Up1", variable=self.Upper1)
		self.w["en_up2"] = ttk.Checkbutton(self.tab[cur_tab], text="Enable Up2", variable=self.Upper2)
		self.w["en_low"] = ttk.Checkbutton(self.tab[cur_tab], text="Enable Low", variable=self.Lower)
		self.w["en_up1"].grid(row=3, column=0, sticky="NSW")
		self.w["en_up2"].grid(row=3, column=1, sticky="NSW")
		self.w["en_low"].grid(row=3, column=2, sticky="NSW")
		self.w["en_up1"].configure(command=self.onEnableUp1, state=['!disabled','selected'] )
		self.w["en_up2"].configure(command=self.onEnableUp2, state=['!disabled','!selected'] )
		self.w["en_low"].configure(command=self.onEnableLow, state=['!disabled','!selected'] )
		# parametri
		self.tparams = [tk.IntVar() for i in range(npar)]
		self.listpar = list(sorted(ToneParams.keys()))
		for i in range(npar):
			tp = ToneParams[ self.listpar[i] ]
			self.w["param" + str(i)] = ttk.Scale(self.tab[cur_tab], from_=tp[1], to=tp[2], variable=self.tparams[i], command=lambda event,j=i : self.onParam(event,j))
			self.w["param" + str(i)].grid(row=4+i, column=0, sticky="WE")
			self.w["parlab" + str(i)] = ttk.Label(self.tab[cur_tab], text=self.listpar[i])
			self.w["parlab" + str(i)].grid(row=4+i, column=1, sticky="W")
		#------
		cur_tab = self.tabs.index("MFX")
		self.tab[cur_tab].rowconfigure(0, weight=1)
		for i in range(16):
			self.tab[cur_tab].rowconfigure(i+1, weight=1)
		self.tab[cur_tab].columnconfigure(0, weight=1)	
		self.tab[cur_tab].columnconfigure(1, weight=1)
		self.tab[cur_tab].columnconfigure(2, weight=1)
		self.tab[cur_tab].columnconfigure(3, weight=1)	
		self.tab[cur_tab].grid(sticky="NSEW")
		self.w["mfx_type"] = ttk.Combobox(self.tab[cur_tab], state=['readonly'])
		self.w["mfx_type"].grid(row=0, column=0, sticky="NS")
		self.w["mfx_type"].bind("<<ComboboxSelected>>", self.onMFX)
		#parametri MFX
		self.mfxparams = [tk.IntVar() for i in range(32)]
		for i in range(32):
			self.w["mfx_param" + str(i)] = ttk.Scale(self.tab[cur_tab], from_=12768, to=52768, variable=self.mfxparams[i], command=lambda event,j=i : self.onMFXParam(event,j))
			self.w["mfx_param" + str(i)].grid(row=1+(i%16), column=0+2*(i//16), sticky="WE")
			self.w["mfx_parlab" + str(i)] = ttk.Label(self.tab[cur_tab], text="Param. "+str(i))
			self.w["mfx_parlab" + str(i)].grid(row=1+(i%16), column=1+2*(i//16), sticky="W")
		######
		for i in range(self.n_tabs):
		 self.nb.add( self.tab[i], text = self.tabs[i] )
		 
	def onMidiPort(self, event):
		self.midiport = self.w["midiport"].current()
		print(self.midiport)
		txt = "Current MIDI Output port:\n" + self.w["midiport"].get()
		self.w["curport"].delete('0.0', tk.END )
		self.w["curport"].insert(tk.END, txt)
		self.w["curport"].update()

	def onChangeScene(self):
		print("Change Scene")
		n = int(self.w["scenenum"].get())
		#print("scene #", n)
		if n >0 and n <= 400:
			x = change_scene_msg(n)
			xl = [y for y in x]
			#print(xl)
			if self.midiport != -1:
				self.mio.openOutputDevice(self.midiport)
				self.mio.sendLongMsg(xl[0:3])
				self.mio.sendLongMsg(xl[3:6])
				self.mio.sendLongMsg(xl[6:])
				self.mio.closeOutputDevice()
	
	def onCategory(self, event):
		cat = self.w["category"].current()
		self.sd.cur_category[self.cur_zone] = cat
		lista_suoni = [ x[0] for x in rd88_sounds[ rd88_categories_s[cat] ] ]
		self.w["tone"].set('')
		self.w["tone"]['values'] = lista_suoni
		self.w["tone"].current(0)
		
	def onTone(self, event):
		cat = self.w["category"].current()
		snd = self.w["tone"].current()
		snd_val = rd88_sounds[ rd88_categories_s[cat] ][snd]
		#print(snd_val)
		self.sd.cur_sound[ self.cur_zone ] = snd
		self.sendTone()
		
	def onZone(self, event):
		z = self.w["zone"].current()
		#print("zone #", z)
		self.cur_zone = z
		# aggiorna category e tone
		cat = self.sd.cur_category[z]
		self.w["category"].current( cat )
		lista_suoni = [ x[0] for x in rd88_sounds[ rd88_categories_s[cat] ] ]
		self.w["tone"].set('')
		self.w["tone"]['values'] = lista_suoni
		self.w["tone"].current( self.sd.cur_sound[z] )
		# aggiorna parametri
		self.recallParams()
	
	def onEnableUp1(self):
		print(self.Upper1.get())
		self.onEnableZone(0, self.Upper1.get())

	def onEnableUp2(self):
		print(self.Upper2.get())
		self.onEnableZone(1, self.Upper2.get())

	def onEnableLow(self):
		print(self.Lower.get())
		self.onEnableZone(2, self.Lower.get())
		
	def onEnableZone(self, z, st):
		self.sd.enabled[z] = st
		zz = ["Zone1", "Zone2", "Zone3"][z]
		a = get_address("Temporary", zz, param=0)
		syx = dt1_message(a, [st])
		#print(syx) # debug
		if self.midiport != -1:
			self.mio.openOutputDevice(self.midiport)
			self.mio.sendLongMsg(syx)
			self.mio.closeOutputDevice()
	
	def onParam(self, event, j):
		k = self.listpar[j]
		val = self.tparams[j].get()
		self.sd.tone_params[self.cur_zone][j] = val
		v1,v2 = ToneParams[k][1], ToneParams[k][2]
		m1,m2 = ToneParams[k][3], ToneParams[k][4]
		mapv = m1 + ( (val - v1) * (m2 - m1) )//(v2 - v1)
		self.w["parlab" + str(j)].configure(text=k + " : " + str(val) + " [" + str(mapv) + "]")
		zz = ["Tone1", "Tone2", "Tone3"][self.cur_zone]
		a = get_address("Temporary", zz, param=ToneParams[k][0])
		#print(zz, hex(a))
		syx = dt1_message(a, [val])
		if self.midiport != -1:
			self.mio.openOutputDevice(self.midiport)
			self.mio.sendLongMsg(syx)
			self.mio.closeOutputDevice()
	
	def onMFX(self, event):
		mfx = self.w["mfx_type"].current()
		zz = ["Tone1", "Tone2", "Tone3"][self.cur_zone]
		a = get_address("Temporary", zz, param=0x1E) # MFX follow
		syx = dt1_message(a, [0])
		if self.midiport != -1:
			self.mio.openOutputDevice(self.midiport)
			self.mio.sendLongMsg(syx)
			self.mio.closeOutputDevice()
		zz = ["MFX1", "MFX2", "MFX3"][self.cur_zone]
		#print(MFXParams[mfx][0], MFXParams[mfx][1][0][0]) # debug
		num_par = len(MFXParams[mfx][1])
		for pp in range(num_par):
			par_conf = MFXParams[mfx][1][pp]
			self.w["mfx_param"+str(pp)].state(["!disabled"])
			self.w["mfx_parlab"+str(pp)].configure(text=par_conf[0])
			rng_par = len(par_conf[1])
			if rng_par > 0:
				self.w["mfx_param"+str(pp)].configure(from_=0, to=rng_par-1)
		for pp in range(num_par, 32):
			self.w["mfx_param"+str(pp)].state(["disabled"])
			self.w["mfx_parlab"+str(pp)].configure(text="n.a.")
		a = get_address("Temporary", zz, param=0) # MFX type
		syx = dt1_message(a, [mfx])
		#print(zz, hex(a), mfx)
		if self.midiport != -1:
			self.mio.openOutputDevice(self.midiport)
			self.mio.sendLongMsg(syx)
			self.mio.closeOutputDevice()
		
	def onMFXParam(self, event, j):
		mfx = self.w["mfx_type"].current()
		val = self.mfxparams[j].get()
		par_conf = MFXParams[mfx][1][j]
		if len(par_conf[1]) == 0:
			v1, v2 = 0, 127 # DA FARE !!! SERVONO I MAPPAGGI CORRETTI !!!
			m1, m2 = 12768, 52768
			#mapv = m1 + ( (val - v1) * (m2 - m1) )//(v2 - v1) # RIVEDERE !!!
			mapv = val
			val_s = str(val)
		else:
			if len(par_conf[2]) > 0:
				mapv = par_conf[2][val]
			else:
				mapv = 32768 + val
			val_s = str(par_conf[1][val])
		self.w["mfx_parlab" + str(j)].configure(text=par_conf[0] + " : " + val_s + " [" + str(mapv) + "]")
		zz = ["MFX1", "MFX2", "MFX3"][self.cur_zone]
		if j < 28:
			a = get_address("Temporary", zz, param=j*4+0x10)
		else:
			a = get_address("Temporary", zz, param=j*4+0x90)
		#print(zz, hex(a))
		tbs = []
		for j in range(4):
			vv = ( mapv >> ((3-j)*4) ) & 0x0F
			tbs.append(vv)
		#print(tbs)	
		syx = dt1_message(a, tbs)
		if self.midiport != -1:
			self.mio.openOutputDevice(self.midiport)
			self.mio.sendLongMsg(syx)
			self.mio.closeOutputDevice()
		
	def initData(self):
		self.w["scenenum"].delete(0)
		self.w["scenenum"].insert(0, "1")
		self.mio = Win32MidiIO()
		self.mio.listOutputDevices()
		self.w["midiport"]['values'] = self.mio.listOut
		self.w["midiport"].current(0)
		self.midiport = -1
		self.w["category"]['values'] = rd88_categories_s
		self.w["category"].current(0)
		lista_suoni = [ x[0] for x in rd88_sounds[ rd88_categories_s[0] ] ]
		self.w["tone"]['values'] = lista_suoni
		self.w["tone"].current(0)
		self.cur_sound = lista_suoni[0]
		self.w["mfx_type"]['values'] = MFXList
		self.w["mfx_type"].current(0)
		self.w["zone"]['values'] = ["UPPER1", "UPPER2", "LOWER"]
		self.w["zone"].current(0)
		self.cur_zone = 0
		# parametri di default
		for z in range(3):
			for i in range(self.sd.nparams):
				k = self.listpar[i]
				pdef = ToneParams[k][5]
				self.sd.tone_params[z][i] = pdef
		for i in range(self.sd.nparams):
			self.w["param"+str(i)].set(self.sd.tone_params[self.cur_zone][i])
		self.midiport = 0	

	def recallParams(self):
		z = self.cur_zone
		for i in range(self.sd.nparams):
			pval = self.sd.tone_params[z][i]
			self.tparams[i].set(pval)
			self.w["param" + str(i)].set( pval )
		
	def sendTone(self):
		self.mio.openOutputDevice(self.midiport)
		#self.mio.debug = True
		cz = self.cur_zone
		cc = self.sd.cur_category[cz]
		cs = self.sd.cur_sound[cz]
		snd_val = rd88_sounds[ rd88_categories_s[cc] ][cs]
		zz = ["Tone1", "Tone2", "Tone3"][cz]
		a = get_address("Temporary", zz, param=0) # Tone bank select MSB
		syx = dt1_message(a, [ snd_val[1] ])
		#print(syx) # debug
		self.mio.sendLongMsg(syx)
		a = get_address("Temporary", zz, param=1) # Tone bank select LSB
		syx = dt1_message(a, [ snd_val[2] ])
		#print(syx) # debug
		self.mio.sendLongMsg(syx)
		a = get_address("Temporary", zz, param=2) # Tone program change (1-based)
		syx = dt1_message(a, [ snd_val[3] - 1 ])
		#print(syx) # debug
		self.mio.sendLongMsg(syx)
		self.mio.closeOutputDevice()

	def sendAllParams(self):
		for cz in range(3):
			self.cur_zone = cz
			self.sendTone()
			self.mio.openOutputDevice(self.midiport)
			for i in range(self.sd.nparams):
				val = self.sd.tone_params[self.cur_zone][i]
				k = self.listpar[i]
				v1,v2 = ToneParams[k][1], ToneParams[k][2]
				m1,m2 = ToneParams[k][3], ToneParams[k][4]
				mapv = m1 + ( (val - v1) * (m2 - m1) )//(v2 - v1)
				self.w["parlab" + str(i)].configure(text=k + " : " + str(val) + " [" + str(mapv) + "]")
				zz = ["Tone1", "Tone2", "Tone3"][self.cur_zone]
				a = get_address("Temporary", zz, param=ToneParams[k][0])
				#print(zz, hex(a))
				syx = dt1_message(a, [val])
				#self.mio.openOutputDevice(self.midiport)
				self.mio.sendLongMsg(syx)
				#self.mio.closeOutputDevice()
			self.mio.closeOutputDevice()		
		
	def onOpen(self):
		nomefile = filedialog.askopenfilename()
		if len(nomefile) > 0:
			self.w["nomefile"].configure(text=nomefile)
			f = open(nomefile, 'rb')
			self.sd = pickle.load(f)
			#print(self.sd)
			f.close()
			self.sendAllParams()

	def onSave(self):
		nomefile = filedialog.asksaveasfilename()
		if len(nomefile) > 0:
			f = open(nomefile, 'wb')
			pickle.dump(self.sd, f)
			f.close()
		
app=Rd88Editor(w=640, h=600)
app.master.title("RD88 Editor")
app.mainloop()