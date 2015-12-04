# prodigy-classic-tools

This repository is for tools aiding the reverse engineering of the 
Prodigy (Classic) Reception System.


Currently there are two Python 3 utilities, viewer and stageutl, that make 
use of a Python 3 library which provides some access to Prodigy's famous 
STAGE.DAT file.

Everything is in the middle of **2** rewrites. (The first rewrite was 
started a couple years ago and then I had to step away. In an attempt to 
get the code semi-decent enough to share, I've started a second re-write.)
So the code could be better and the bugs are bountiful. Oh, and did I 
mention that I barely have any documentation regarding the insides of 
Prodigy? That doesn't help things either.


## viewer utility 

This is a sometimes fun utility for trying to get the Prodigy Reception 
System (RS.EXE, the Prodigy client) to execute program objects stored in a
STAGE.DAT file and put some pretty 
[NAPLPS](https://en.wikipedia.org/wiki/NAPLPS) text and graphics on the 
screen. This is what has been used to produce most of the Prodigy screen
shots you may have seen.

This very simple utility works by getting a list of desired objects from
STAGE.DAT and creates a MS-DOS batch file. You would then run this batch
file under something like [DOSBox](https://en.wikipedia.org/wiki/DOSBox)
and it will get the Reception System to load and execute each object in
turn. Then, sometimes, something pretty will momentarily pop up on the
screen.

A common invocation would be `viewer --obj-type 4 --prompt STAGE.DAT`.
This will create VIEW.BAT. You would then start DOSBox, go into the 
Prodigy directory, and run VIEW. Hopefully, before too many objects,
you'll see something worth while. If it hangs you can check OBJECTS.LOG to
see the number of the problem object. Passing that number +1 to VIEW will
jump directly to that object, bypassing the hanging object.


## stageutl utility

This is a much more advanced utility. It can take a few different
sub-commands, which I'll now very briefly cover.


### stageutl show-aum

STAGE.DAT is very close to a standard FAT file system. This will show how
it's being used. (I got the idea from the 
[TRSDOS](https://en.wikipedia.org/wiki/TRS-DOS) "free" command.)

`stageutl show-aum STAGE.DAT` will produce something like:
```
  0x0:   X   X   -   %   -   -   -   -   -   -   -   -   -   -   -   -  
 0x10:   -   -   -   -   -   -   -   -   -   %   -   -   -   -   -   -  
 0x20:   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
 0x30:   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
 0x40:   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
 0x50:   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
 0x60:   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
 0x70:   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
 0x80:   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
 0x90:   %   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
 0xa0:   -   -   -   -   -   -   %   -   -   -   -   -   -   -   -   -  
 0xb0:   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
 0xc0:   -   -   -   -   -   -   -  123  -   -   -   -   -   -   -   - 
```
...
```
0xdb0:   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U  
0xdc0:   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U  
0xdd0:   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U  
0xde0:   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U  
0xdf0:   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U  
0xe00:   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U  
0xe10:   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U  
0xe20:   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U  
0xe30:   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U  
0xe40:   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U  
0xe50:   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U  
0xe60:   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U  
0xe70:   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U   U
```

The X's indicate non-existent “allocation units”. Hyphens (-) indicate
the next AU in an object's chain is the one to the right. A percent 
sign (%) indicates the end of a chain. If it's a number then it indicates
fragmentation and that number is the next AU in the chain. Finally, a 
U means it's not currently allocated. 


### stageutl dir

And just like any file system, you need a way to see the objects contained
within it. 

`stageutl dir STAGE.DAT` gives a detailed directory listing:
```
line      name     loc type   length   stat auid  ver stor check ssize
0001  2A00APPL.PG   1    4   49(   73)    1  70e  202   1f  df1f     1
0005  2A00GATE.PGM  0    c  7b4( 1972)    1  70f  4c7    8  1e0f     0
0007  2A00LVER.BDY  0    8  515( 1301)    1  717  68f    7  cfd1     0
0016  2A00LVER.PGM  0    c   40(   64)    1  71d  447    5  0b3e     0
0018  4A001000.BDY  0    8  4b1( 1201)    1  755  432    0  453f     0
0092  4A001000.MEN  0    4   9f(  159)    1  754  417    0  c382     0
0097  4A00HSEL.PGM  0    c   3f(   63)            338    0           0
0101  4A00ADOM.WND  0    e  326(  806)    1  774  43a    0  b660     0
0136  4A00ADWI.PGM  0    c  316(  790)    1  779  432    0  99a5     1
0138  4A00ADWP.PGM  0    c  670( 1648)    1  77d  432    0  5220     1
0140  4A00AUTO.PGM  0    c   b3(  179)    1  75c  417    0  0158     0
0142  4A00BIAD.PGM  0    c  315(  789)    1  7b2  432    0  b9d5     1
0144  4A00CKCM.PGM  0    c  613( 1555)    1  76d  432    0  5c86     1
0146  4A00CURS.PGM  0    c   1d(   29)    1  778  422    0  05a4     0
0148  4A00DREC.WND  0    e  122(  290)    1  795  422    0  4a54     0
0158  4A00ENTR.PGM  0    c  65e( 1630)    1  749  432    0  6a7c     1
```
...

The various columns are too technical to get into now. But I will tell you
that when you see an object without an allocation unit ID (AUID), nothing
is wrong. It simply means it's embedded in a prior object. So above, 
4A00HSEL.PGM is inside of 4A001000.MEN.


### stageutl view

This is a cool looking tool that will output data about objects in
STAGE.DAT. Objects are made up of segments. When I know what a piece of
data is, I try to parse it. Otherwise it is dumped raw. But hex dumps are
sexy so there's nothing wrong with that.

`stageutl view STAGE.DAT` outputs something like:
```
0001 2A00APPL.PG 1 0x4   length=0x49(73) status=0x1 startid=0x70e(1806)
     -       version=0x202 store_candidacy=31 check=0xdf1f setsize=1
0002 |   PageFormatCallSegment   st=0x31 sl=0x11(17)
     |   |   id              : XXOF0010.FMT 0x0 0x0
     |   |   parm            : None
     |   |   parm_length     : None
     |   |   prefix          : 0xd     (13)
0003 |   ElementCallSegment   st=0x21 sl=0x13(19)
     |   |   id              : 2A000251.HDR 0x0 0x8
     |   |   parm            : None
     |   |   parm_length     : None
     |   |   part_id         : 0x1     (1)
     |   |   prefix          : 0xd     (13)
     |   |   priority        : 0x0     (0)
0004 |   SelectorCallSegment   st=0x20 sl=0x13(19)
     |   |   id              : 2A00GATE.PGM 0x0 0xc
     |   |   parm            : None
     |   |   parm_length     : None
     |   |   part_id         : 0x2     (2)
     |   |   prefix          : 0xd     (13)
     |   |   priority        : 0x0     (0)

0005 2A00GATE.PGM 0 0xc   length=0x7b4(1972) status=0x1 startid=0x70f(1807)
     -       version=0x4c7 store_candidacy=8 check=0x1e0f setsize=0
0006 |   ProgramDataSegment   st=0x61 sl=0x7a2(1954)
     |   |   data            : (1950 bytes) 
  0000  00 00 14 00 02 07 50 41  4c 43 48 41 54 33 0b 43  |......PALCHAT3.C|
  0010  48 41 54 50 52 4f 46 49  4c 45 0e 7e 0f 26 0a 00  |HATPROFILE.~.&..|
  0020  74 26 13 61 b6 07 00 05  1a 1e 6d bb 7f 04 00 13  |t&.a......m.....|
  0030  8e 06 17 79 13 c3 01 20  00 5b 13 5e b5 0f 00 05  |...y... .[.^....|
  0040  50 00 07 39 2e 31 37 2e  31 34 6f bb 7f 16 00 00  |P..9.17.14o.....|
  0050  0d 32 41 30 30 49 4e 49  54 50 47 4d 00 0c de 00  |.2A00INITPGM....|
  0060  7d 1b 00 26 01 85 03 00  0d 32 41 30 30 4c 56 45  |}..&.....2A00LVE|
  0070  52 42 44 59 00 08 dd 03  c1 06 13 8e 28 00 0d 45  |RBDY........(..E|
  0080  34 41 30 30 32 35 31 48  44 52 00 08 29 00 00 07  |4A00251HDR..)...|
```
...


### stageutl extract

This *will* allow the extraction of attributes from segments, segments
from objects, and objects from the STAGE.DAT file. It is currently a
victim of one of the rewrites I mentioned above. I'm not even sure it
works. I'm not going to describe it now.
