/*
 *  Debug_GetPCFromUContext.cpp
 *  code taken from OpenLieroX
 *
 *  Created by Albert Zeyer on 06.04.12.
 *  Originally under LGPL, but effectively the source was taken from public domain
 *  and modified only by me, so let it be under BSD licence here.
 *
 */

#ifdef WIN32
void* GetPCFromUContext(void* ucontext) { return 0; }

#else

#include <signal.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <ctype.h>
#include <unistd.h>

#if defined(__linux__) || defined(__APPLE__)
/* get REG_EIP / REG_RIP from ucontext.h */
#ifndef _XOPEN_SOURCE
#define _XOPEN_SOURCE
#endif
#include <ucontext.h>
#endif

#ifndef EIP
#define EIP     14
#endif

#if (defined (__x86_64__))
#ifndef REG_RIP
#define REG_RIP REG_INDEX(rip) /* seems to be 16 */
#endif
#endif


void* GetPCFromUContext(void* secret) {
	/* 
	 see this article for further details: (thanks also for some code snippets)
	 http://www.linuxjournal.com/article/6391 */
	
	void *pnt = NULL;
#if defined(__APPLE__)
#	if defined(__x86_64__)
	ucontext_t* uc = (ucontext_t*) secret;
	pnt = (void*) uc->uc_mcontext->__ss.__rip ;
#	elif defined(__hppa__)
	ucontext_t* uc = (ucontext_t*) secret;
	pnt = (void*) uc->uc_mcontext.sc_iaoq[0] & ~0x3UL ;
#	elif (defined (__ppc__)) || (defined (__powerpc__))
	ucontext_t* uc = (ucontext_t*) secret;
#		if __DARWIN_UNIX03
	pnt = (void*) uc->uc_mcontext->__ss.__srr0 ;
#		else
	pnt = (void*) uc->uc_mcontext->ss.srr0 ;
#		endif
#	elif defined(__sparc__)
	struct sigcontext* sc = (struct sigcontext*) secret;
#		if __WORDSIZE == 64
	pnt = (void*) sc->sigc_regs.tpc ;
#		else
	pnt = (void*) sc->si_regs.pc ;
#		endif
#	elif defined(__i386__)
	ucontext_t* uc = (ucontext_t*) secret;
#		if __DARWIN_UNIX03
	pnt = (void*) uc->uc_mcontext->__ss.__eip ;
#		else
	pnt = (void*) uc->uc_mcontext->ss.eip ;
#		endif
#	else
#		warning mcontext is not defined for this arch, thus a dumped backtrace could be crippled
#	endif
#elif defined(__linux__)
#	if defined(__x86_64__)
	ucontext_t* uc = (ucontext_t*) secret;
	pnt = (void*) uc->uc_mcontext.gregs[REG_RIP] ;
#	elif defined(__hppa__)
	ucontext_t* uc = (ucontext_t*) secret;
	pnt = (void*) uc->uc_mcontext.sc_iaoq[0] & ~0x3UL ;
#	elif (defined (__ppc__)) || (defined (__powerpc__))
	ucontext_t* uc = (ucontext_t*) secret;
	pnt = (void*) uc->uc_mcontext.regs->nip ;
#	elif defined(__sparc__)
	struct sigcontext* sc = (struct sigcontext*) secret;
#		if __WORDSIZE == 64
	pnt = (void*) sc->sigc_regs.tpc ;
#		else
	pnt = (void*) sc->si_regs.pc ;
#		endif
#	elif defined(__i386__)
	ucontext_t* uc = (ucontext_t*) secret;
	pnt = (void*) uc->uc_mcontext.gregs[REG_EIP] ;
#	else
#		warning mcontext is not defined for this arch, thus a dumped backtrace could be crippled
#	endif
#else
#	warning mcontest is not defined for this system, thus a dumped backtraced could be crippled
#endif
	
	/* potentially correct for other archs:
	 * alpha: ucp->m_context.sc_pc
	 * arm: ucp->m_context.ctx.arm_pc
	 * ia64: ucp->m_context.sc_ip & ~0x3UL
	 * mips: ucp->m_context.sc_pc
	 * s390: ucp->m_context.sregs->regs.psw.addr
	 */
	
	return pnt;
}

#endif
