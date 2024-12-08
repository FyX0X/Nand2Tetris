// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Fill.asm

// Runs an infinite loop that listens to the keyboard input. 
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed, 
// the screen should be cleared.

	@fill
	M=0
	@i
	M=0
	@addr
	M=0

(LOOP)
	@i
	M=0

	// Check for Keyboard press
	@KBD
	D=M
	@WHITE
	D;JEQ
	@BLACK
	0;JMP

(WHITE)
	@fill
	M=0
	@SCREEN_FILL_LOOP
	0;JMP

(BLACK)
	@fill
	M=-1
	@SCREEN_FILL_LOOP
	0;JMP

(SCREEN_FILL_LOOP)
	// gets current pixel array address
	@SCREEN
	D=A
	@i
	D=D+M
	@addr
	M=D
	
	@fill
	D=M 	// get color
	@addr
	A=M    	// set address
	M=D 	// set color

	// increments i
	@i
	M=M+1

	// loops
	@8096
	D=A
	@i
	D=D-M
	@LOOP
	D;JEQ 	// goto loop if finished
	@SCREEN_FILL_LOOP
	0;JMP
