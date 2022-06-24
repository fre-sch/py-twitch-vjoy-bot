*****
Goals
*****

* Virtual XBox Controller controlled by Python code
* IRC Bot to trigger virtual controller input
* Visuals

=================================================
Virtual XBox Controller controlled by Python code
=================================================

Using http://vjoystick.sourceforge.net/site/index.php/vxbox
Created a Python wrapper for DLL using ctypes.


===========================================
IRC Bot to trigger virtual controller input
===========================================

Bot runs a rolling poll for next input based on chat input.

Once the poll rolls over, the top-most input is sent through the controller
emulation.

Rolling Poll
------------
Poll rate

Roll-Over
"""""""""
Winning command is executed.
* Execute continously
* Execute once

Options after command execution:
* Set vote count to zero
* Set vote count to half or some other fraction
* Decrease vote count over time

Unused Votes
""""""""""""
* Set vote count to zero
* Keep vote count
* Decrease vote count over time

Commands
--------

Buttons:
""""""""
* !a
* !b
* !x
* !y
* !lb
* !rb
* !up
* !down
* !left
* !right
* !ls [click, N, E, S, W, NE, NW, SE, NNE, ENE, ESE, SSE, SSW, WSW, WNW, NNW] (maybe support analog)
* !rs [click, N, E, S, W, NE, NW, SE, NNE, ENE, ESE, SSE, SSW, WSW, WNW, NNW] (maybe support analog)
* !lt (maybe support analog)
* !rt (maybe support analog)


=======
Visuals
=======

* Display time to poll roll over as text, and as timer bar
* Display command votes from most votes (top) to least votes (bottom)
