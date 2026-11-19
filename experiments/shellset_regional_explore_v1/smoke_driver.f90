! Single invocation of the full SHELLS routine using native input readers.
program regional_smoke
  use SHELLS, only: Shells_v5p0
  use SharedVars
  use ShellSetSubs, only: ReadPm, ArcanaShellsInspectFEG, ArcanaShellsFailed, ArcanaShellsRelease
  implicit none
  real(8) :: values(1)
  character(len=10) :: overrides(1)
  logical :: converged, fatal
  integer :: slot
  ThID = 0
  Verbose = .false.
  offMax = 0d0
  open(3,file='engineering.in',status='old',action='read')
  open(21,file='shells.log',status='new')
  call ReadPm(3,21,names,nPlate,offMax,aCreep,alphaT,bCreep,Biot,Byerly, &
       cCreep,cFric,conduc,dCreep,eCreep,everyP,fFric,gMean,gradie,iConve, &
       iPVRef,maxItr,okDelV,okToQt,oneKm,radio,radius,refStr,rhoAst,rhoBar, &
       rhoH2O,tAdiab,tauMax,temLim,title3,trHMax,tSurf,vTimes,zBAsth,pltRef)
  inquire(file='FatalError.txt',exist=fatal)
  if (fatal) stop 1
  ! Runtime-only plate lookup. Slot AF encloses this patch; the other
  ! 51 mandatory legacy outlines enclose an empty, faraway region.
  ! No tabulated Earth angular velocity participates in this test.
  omega = 0d0
  open(8,file='lookup.dig',status='new')
  do slot=1,nPlate
    write(8,'(A2)') names(slot)
    if (names(slot) == 'AF') then
      write(8,'(A)') '-155,-1','-143,-1','-143,8','-155,8','-155,-1'
    else
      write(8,'(A)') '20,20','21,20','21,21','20,21','20,20'
    end if
    write(8,'(A)') '***'
  end do
  rewind(8)
  open(1,file='regional.feg',status='old',action='read')
  call ArcanaShellsInspectFEG(1,'regional_PRE.dat',1)
  open(2,file='engineering.bcs',status='old',action='read')
  open(22,file='velocity.22',status='new')
  open(23,file='reactions.23',status='new')
  open(24,file='torques.24',status='new')
  values = 0d0
  overrides = ""
  converged = .true.
  call Shells_v5p0(overrides(:0),values(:0),1,converged)
  inquire(file='FatalError.txt',exist=fatal)
  if (fatal .or. ArcanaShellsFailed() .or. .not. converged) stop 2
  call ArcanaShellsRelease()
  print '(A)', 'ENGINEERING_SHELLS_CONVERGED'
end program
