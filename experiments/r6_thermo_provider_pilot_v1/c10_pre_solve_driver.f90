! C10 native input probe. The linked SHELLS probe ends before Pure.
program c10_pre_solve_only
  use SHELLS, only: Shells_v5p0
  use SharedVars
  use ShellSetSubs, only: ReadPm, ArcanaShellsInspectFEG, ArcanaShellsFailed
  implicit none
  real(8) :: values(1)
  character(len=10) :: overrides(1)
  character(len=80) :: control
  logical :: completed, fatal
  integer :: slot

  ThID = 0
  Verbose = .false.
  offMax = 0d0
  open(18,file='runtime.control',status='old',action='read')
  read(18,'(A)') control
  close(18)
  if (control /= 'C10_PRE_SOLVE_ONLY') stop 12
  ! RF is the original array slot 1, representing the canonical frame
  ! bookkeeping origin. No Earth rotation/geometry is provided to the probe.
  names(1) = 'RF'
  do slot=0,11
    write(names(slot+2),'(A,I1)') 'R',mod(slot,10)
    if (slot>=10) write(names(slot+2),'(A,I1)') 'S',mod(slot,10)
  end do
  omega = 0d0
  open(3,file='regional.in',status='old',action='read')
  open(21,file='pre_solve.log',status='new')
  call ReadPm(3,21,names,nPlate,offMax,aCreep,alphaT,bCreep,Biot,Byerly, &
       cCreep,cFric,conduc,dCreep,eCreep,everyP,fFric,gMean,gradie,iConve, &
       iPVRef,maxItr,okDelV,okToQt,oneKm,radio,radius,refStr,rhoAst,rhoBar, &
       rhoH2O,tAdiab,tauMax,temLim,title3,trHMax,tSurf,vTimes,zBAsth,pltRef)
  inquire(file='FatalError.txt',exist=fatal)
  if (fatal) stop 13
  if (iConve/=0 .or. trHMax/=0d0 .or. iPVRef/=iPAfri .or. pltRef/='RF') stop 14
  if (int(zBAsth/oneKm+0.5d0)<1) stop 15
  if (Biot/=1d0 .and. Biot/=0d0) stop 16
  open(1,file='regional.feg',status='old',action='read')
  call ArcanaShellsInspectFEG(1,'regional_PRE.dat',1)
  if (ArcanaShellsFailed()) stop 17
  open(2,file='controlled.bcs',status='old',action='read')
  open(8,file='regional_reporting_plates.dat',status='old',action='read')
  values = 0d0
  overrides = ''
  completed = .false.
  call Shells_v5p0(overrides(:0),values(:0),1,completed)
  ! The truncated engineering probe must stop inside Shells_v5p0.
  stop 18
end program
