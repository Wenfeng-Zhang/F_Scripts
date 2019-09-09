# Copyright (c) 2007 The Foundry Visionmongers Ltd.  All Rights Reserved.

# This function is called when the user drag'n'drops or pastes
# anything that looks like a filename on the main window.

proc drop {text} {
  foreach f [split $text "\r\n"] {
    set f [string trim $f]
    if {$f=={}} continue

    # strip the Linux 'file:' prefix
    if [string match "file:*" $f] {
      set f [string range $f 5 end]
    }

    # strip Linux '///' to '/'
    if [string match "///*" $f] {
      set f [string range $f 2 end]
    }

    #set f [filename_fix $f]
    if [file isdirectory $f] {
      # load all images in this directory
      set ff [filename_list -compress $f]
      foreach t $ff {
        set t [string trim $t]
        set subname [file dirname $f/.]/$t
        #set subname $f/$t

        if [file isdirectory $subname] {
          set fff [filename_list -compress $subname]
          foreach tt $fff {
            set tt [string trim $tt]
            if [string match "*.db" $tt] {
              continue
            } elseif [string match "*.tmp" $tt] {
              continue
            } else {
              set subsubname [file dirname $subname/.]/$tt
              if [file isdirectory $subsubname] {
                set ffff [filename_list -compress $subsubname]
                foreach ttt $ffff {
                  set ttt [string trim $ttt]
                  if [string match "*.db" $ttt] {
                    continue
                  } elseif [string match "*.tmp" $ttt] {
                    continue
                  } else {
                    set subsubsubname [file dirname $subsubname/.]/$ttt
                    Read -New file $subsubsubname
                  }
                }
              } else {
                Read -New file $subsubname
              }
            }
          }
        } else {
          Read -New file $subname
        }
      }
    } elseif [regexp {.\.((nk[34])|(nk)|(nuke)|(nuke[34]))$} $f] {
      scriptReadFile $f
    } elseif [regexp {.\.((nk[34])|(nk)|(nuke)|(nuke[34])).autosave$} $f] {
      scriptReadFile $f
    } else {
      Read -New file $f
    }
  }
}
