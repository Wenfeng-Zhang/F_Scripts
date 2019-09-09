#-*- coding:utf8 -*-
#__author__ = 'wenfeng zhang'
#https://github.com/Wenfeng-Zhang
# data: 2019/4/13

'''
import FileCopy
toolbar = nuke.menu("Nodes")
m = toolbar.addMenu('F Script',)
m.addCommand("FileCopy" ,"FileCopy.main()","shift+C",icon="Write.png")
'''

import nuke
import os, re, subprocess
import threading

#序列的格式，用于分别序列和视频
SEQUENCE = ['.cin', '.dpx', '.exr', '.fpi', '.hdr', '.jpg', '.jpeg', '.null', '.pic', '.png', '.sgi', '.tga', '.targe',
            '.tif', '.tiff', '.xpm', '.yuv']

#正则，用于提取文件名以及判断文件夹里的文件是否都为选中的。
REGEXP = '(.*)(%\d*d)'

#默认的输出路径
OUTPUT_PATH = r'D:\default_output_path'

#主类，调用多线程函数。
class Filecopy(threading.Thread):
    def __init__(self, nodes):
        threading.Thread.__init__(self)
        self.selected_nodes = nodes
        if not nodes:
            nuke.message('No nodes are selected.')
            self.panel_bool = False
            return None
            
        for node in nodes:
            if node.Class() == 'Read':  
                self.Panel()
                return None
            continue
            
        nuke.message("There are no read nodes.")
        self.panel_bool = False
        
    #对话框
    def Panel(self):
        p = nuke.Panel('Copy file to specified path')

        p.addFilenameSearch('Output Path:', OUTPUT_PATH)
        p.addBooleanCheckBox('Do you open folders by copying them?', True)
        p.addButton('cannle')
        p.addButton('Copy')
        p.setWidth(500)

        if p.show():
            self.panel_bool = True
            self.open_bool = p.value('Do you open folders by copying them?')
            self.output_Path = p.value('Output Path:')
        else:
            self.panel_bool = False

    #统计选中的Read中的文件数量，用以去掉重复路径。
    def selectedNodes_number_files(self):
        number_of_files = 0
        filelist = []
        for node in self.selected_nodes:
            if node.Class() != "Read":
                continue
            filename = node.knob('file').getValue()
            if filename not in filelist:
                extension = os.path.splitext(filename)[-1]
                if extension in SEQUENCE:
                    first = node.knob('first').value()
                    last = node.knob('last').value()
                    num = last - first + 1
                    number_of_files += num
                else:
                    number_of_files += 1
        return number_of_files

    #根据格式分别对每个素材创建相对应的路径和CMD命令
    def create_commands_and_paths(self):
        path_dict = dict()
        name_dict = dict()
        for node in self.selected_nodes:
            full_file_path = node.knob('file').getValue()
            nodes_folder = os.path.dirname(full_file_path)
            full_file_name = os.path.basename(full_file_path)
            folder_name = os.path.basename(nodes_folder)
            file_type = os.path.splitext(full_file_path)[-1]

            m = re.search(REGEXP, full_file_path)
            if m:
                regexp_file = os.path.basename(m.group(1))
                output_file_path = os.path.join(self.output_Path, folder_name)
                new_REGEXP = ''.join((regexp_file, '*', file_type))
                cmd = 'robocopy "%s" "%s" %s /NP /NJS /NJH /NS /NC' % (nodes_folder, output_file_path, new_REGEXP)
                path_dict[cmd] = output_file_path
                name_dict[cmd] = folder_name

            else:
                output_file_path = self.output_Path
                cmd = 'robocopy "%s" "%s" %s /NP /NJS /NJH /NS /NC' % (nodes_folder, output_file_path, full_file_name)
                path_dict[cmd] = output_file_path
                name_dict[cmd] = full_file_name
        return path_dict,name_dict

    #复制函数，运用subprocess模块调用window系统自带的robocopy来复制，并实时生成进度条
    def copy_file(self):
        numberAll = self.selectedNodes_number_files()
        path_dict,name_dict = self.create_commands_and_paths()
        
        number = 0
        file_bool = True

        if not file_bool:
            return None
        task = nuke.ProgressTask('Copy files')
                
        for cmd, output_file_path in path_dict.items():
            if file_bool:
                if not os.path.exists(output_file_path):
                    os.makedirs(output_file_path)
                child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
                while child.poll() is None:
                    line = child.stdout.readline().strip()
                    line_ext = os.path.splitext(line)[-1]
                    if line_ext:
                        number += 1
                    if line_ext not in SEQUENCE:
                        line = name_dict[cmd]
                    task.setMessage('Copy ''{}'' files   ''{}'.format(numberAll, line))
                    percentage = int((float(number) / numberAll) * 100)
                    task.setProgress(percentage)

                    if task.isCancelled():
                        file_bool = False
                        child.terminate()
                        break
                    print('   '.join((line, 'to', output_file_path)))

                if self.open_bool and os.path.exists(output_file_path):
                    self.open_folder(output_file_path)                
            else:
                break

    #打开文件夹
    def open_folder(self,path):
        import sys
        if (sys.platform == 'win32'):
            cmd = 'start "" "%s"' % path
            os.system(cmd)
                
    #运用多线程调取命令
    def run(self):
        if self.panel_bool:
            self.copy_file()

def main():
    nodes = nuke.selectedNodes()
    filecopy = Filecopy(nodes)
    filecopy.start()

if __name__ == "__main__":
    main()
