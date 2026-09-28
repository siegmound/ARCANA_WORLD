program open_pair_driver
  use ShellSetSubs, only: OpenInput, CloseInput
  implicit none
  character(len=400) :: root
  call get_command_argument(1,root)
  call OpenInput(1,1,"OD",trim(root))
  call CloseInput("OD")
  print '(A)',"ORBDATA_INPUT_PAIR_OPEN_CLOSE=PASS"
end program open_pair_driver
