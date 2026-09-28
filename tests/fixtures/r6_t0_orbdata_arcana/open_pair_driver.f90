! Test-only end-to-end InputSetup -> OpenInput -> CloseInput fixture.
program inputsetup_pair_driver
  use ShellSetSubs, only: InputSetup, OpenInput, CloseInput
  implicit none
  character(len=100) :: root, mode
  logical :: has12, has15, has16
  call get_command_argument(1,root)
  call get_command_argument(2,mode)
  call InputSetup(1,1,"OD",trim(root))
  inquire(file=trim(root)//"/ThID_1_Data_input/fort_1.12",exist=has12)
  inquire(file=trim(root)//"/ThID_1_Data_input/fort_1.15",exist=has15)
  inquire(file=trim(root)//"/ThID_1_Data_input/fort_1.16",exist=has16)
  select case(trim(mode))
  case("stock")
    if (.not. has12 .or. has15 .or. has16) error stop "stock staging contract failed"
  case("full")
    if (has12 .or. .not. has15 .or. .not. has16) error stop "ARCANA staging contract failed"
  case default
    error stop "fixture mode must be stock or full"
  end select
  call OpenInput(1,1,"OD",trim(root))
  call CloseInput("OD")
  print '(A,A)',"INPUTSETUP_OPEN_CLOSE_FIXTURE=PASS mode=",trim(mode)
end program inputsetup_pair_driver
