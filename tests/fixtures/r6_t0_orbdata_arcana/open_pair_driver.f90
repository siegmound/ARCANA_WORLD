! Test-only end-to-end InputSetup -> OpenInput -> CloseInput fixture.
program inputsetup_pair_driver
  use ShellSetSubs, only: InputSetup, OpenInput, CloseInput
  implicit none
  character(len=100) :: root, mode
  logical :: has12, has15, has16, fatal_exists, detail_exists, found_detail
  integer :: io_status
  character(len=512) :: line
  call get_command_argument(1,root)
  call get_command_argument(2,mode)
  call InputSetup(1,1,"OD",root)
  if (trim(mode)=="partial") then
    inquire(file="FatalError.txt",exist=fatal_exists)
    inquire(file="Error/FatalError_1.txt",exist=detail_exists)
    if (.not. fatal_exists .or. .not. detail_exists) &
         error stop "InputSetup did not record both FatalError files"
    open(unit=91,file="Error/FatalError_1.txt",status="old",action="read")
    found_detail=.false.
    do
      read(91,'(A)',iostat=io_status) line
      if (io_status/=0) exit
      if (index(line,"Incomplete ARCANA OrbData source pair")>0) found_detail=.true.
    end do
    close(91)
    if (.not. found_detail) error stop "detailed FatalError lacks partial-pair reason"
    print '(A)',"INPUTSETUP_PARTIAL_PAIR_FATAL_RECORDED=PASS"
    stop
  end if
  inquire(file=trim(root)//"/ThID_1_Data_input/fort_1.12",exist=has12)
  inquire(file=trim(root)//"/ThID_1_Data_input/fort_1.15",exist=has15)
  inquire(file=trim(root)//"/ThID_1_Data_input/fort_1.16",exist=has16)
  select case(trim(mode))
  case("stock")
    if (.not. has12 .or. has15 .or. has16) error stop "stock staging contract failed"
  case("full")
    if (has12 .or. .not. has15 .or. .not. has16) error stop "ARCANA staging contract failed"
  end select
  call OpenInput(1,1,"OD",root)
  call CloseInput("OD")
  print '(A,A)',"INPUTSETUP_OPEN_CLOSE_FIXTURE=PASS mode=",trim(mode)
end program inputsetup_pair_driver
