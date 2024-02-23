import struct

prefix_dt1 = struct.pack('B'*8, 0xF0, 0x41, 0x10, 0x00, 0x00, 0x00, 0x64, 0x12)
eox = struct.pack('B', 0xF7)

# converte intero di 4 bytes in bytes (packed)
def address(x):
	return  struct.pack('>I', x) # MSB .. LSB (big endian)
	
# converte lista di interi (0-255) in	bytes
def data(x):
	l = len(x)
	if l > 0:
		r = struct.pack('B', x[0])
		for i in range(1,l):
			r += struct.pack('B', x[i])
	else:
		r = None
	return r	
	
# checksum su un array di bytes	ottenuto con pack
def checksum(x):
	l = len(x)
	y = struct.unpack('B'*l, x)
	sum = 0
	for z in y:
		sum += z
	r = sum % 128
	r = 128 - r
	return struct.pack('B', r)
	
# costruisce messaggio da indirizzo (32 bit) e dati (lista di interi a 8 bit)	
def dt1_message(a, d):
	aa = address(a)
	dd = data(d)
	return prefix_dt1 + aa + dd + checksum(aa+dd) + eox
	
base_address = { "System" : (0x00000000, "System"), "Temporary" : (0x01000000, "Scene"), 
	"Setup" : (0x02000000, "Setup"), "User" : (0x10000000, "Scene") }
	
sub_address_system = { "Common" : 0x000000, "Control" : 0x000100, "Chorus" : 0x000200, "Reverb" : 0x000300,
 "EQ" : 0x000400, "Comp" : 0x000500, "Input Reverb" : 0x000600, "Input EQ" : 0x000700 }
 
sub_address_scene = { "Common" : 0x000000, 
 "Tone1" : 0x001000, "Tone2" : 0x001100, "Tone3" : 0x001200,
 "EQ1" : 0x002000, "EQ2" : 0x002100, "EQ3" : 0x002200, 
 "MFX1" : 0x003000, "MFX2" : 0x003200, "MFX3" : 0x003400, 
 "Zone1" : 0x004000, "Zone2" : 0x004100, "Zone3" : 0x004200,
 "IFX": 0x005000, "Chorus" : 0x005200, "Reverb" : 0x005300, "SympRes" : 0x005400
 }

sub_address_setup = { "Setup" : 0x000000 }

subaddr = { "System" : sub_address_system, "Scene" : sub_address_scene, "Setup" : sub_address_setup }

USER_SCENE_DELTA = 0x10000

# indirizzo a partire dalla "sezione", "sub-sezione", numero di scena eventuale (1-based) e numero di parametro
def get_address(sect="Temporary", sub="Tone1", scene=1, param=0):
	if sect not in base_address:
		return 0xFFFFFFFF
	ba = base_address[ sect ][0]
	subtype = base_address[ sect ][1]
	sa_list = subaddr[ subtype ]
	if sub in sa_list:
		#print( "Section:", sect, "Subaddress type:", sub, "Address:", hex(sa_list[sub]) ) # debug
		a = ba + sa_list[ sub ]
	else:
		a = ba
	if sect == "User":
		a = a + (scene-1)*USER_SCENE_DELTA
	return a + param
	
def change_scene_msg(scene=1):
	bank = ( scene - 1 ) // 128
	pc = ( scene - 1 ) % 128	
	bank_sel = struct.pack('B', 0xBF)
	prog_ch = struct.pack('B', 0xCF)
	xx = bank_sel + struct.pack('BB', 0x00, 0x55)
	xx = xx + bank_sel + struct.pack('B', 0x20) + struct.pack('B', bank)
	xx = xx + prog_ch + struct.pack('B', pc)
	return xx
	
def tests():
	print( sub_address_scene.keys() )
	print(prefix_dt1+address(0x010203)) # concatenazione di array ottenuti con pack
	print(checksum( struct.pack('B'*5, 0x01,0x00,0x00,0x10,0x4A)) )
	print(prefix_dt1+address(0x000000 + 0x0102) + data( [1,2,3,4,5] ) )
	print(dt1_message(0xA01000f5, [9,8,7,6]))
	print( address(get_address("Temporary", "EQ3")) )
	aa = address(get_address("User", "EQ3", scene=341, param = 0x10))
	print( [hex(z) for z in aa] )
	print( [hex(z) for z in change_scene_msg( 200 )] )
	
#tests()	
