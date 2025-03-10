﻿using System;
using System.IO;
using System.Windows.Forms;

namespace TCFontCreator
{
    public partial class FormMain : Form
    {
        public FormMain(string[] args)
        {
            showCMD = args.Length > 0 && args[0].ToLower() == "cmd";
            InitializeComponent();
        }

        private readonly bool showCMD;
        private string exeffpy;
        private string exepy;
        private string path;
        private string fileout;
        private bool isotcff;
        private System.Threading.Thread thRun;
        private string err;
        private string outinfo;
        private string cmdline;

        private void FormMain_Load(object sender, EventArgs e)
        {
            comboBoxSys.SelectedIndex = 0;
            comboBoxApp.SelectedIndex = 0;
            comboBoxVar.SelectedIndex = 0;
            comboBoxMulti.SelectedIndex = 1;
            panel1.Enabled = checkBoxInfo.Checked;
            CheckForIllegalCrossThreadCalls = false;
        }

        private void SetExec()
        {
            exeffpy = path + "FontForgeBuilds/bin/ffpython.exe";
            exepy = path + "python/python.exe";
            if (System.IO.File.Exists("appdata"))
            {
                string[] str = System.IO.File.ReadAllLines("appdata");
                foreach (string item in str)
                {
                    string line = item.Trim();
                    if (!line.StartsWith("#") && line.Contains("="))
                    {
                        string[] finfo = line.Split('=');
                        if (finfo[0].Trim().ToLower() == "fontforge")
                        {
                            string f = finfo[1].Trim().Replace("\\", "/");
                            if (f.ToLower().EndsWith("fontforge.exe"))
                            {
                                string file = f.Substring(0, f.LastIndexOf('/') + 1) + "ffpython.exe";
                                if (System.IO.File.Exists(file))
                                {
                                    exeffpy = file;
                                }
                            }
                            else if (f.ToLower().EndsWith("ffpython.exe"))
                            {
                                if (System.IO.File.Exists(f))
                                {
                                    exeffpy = f;
                                }
                            }
                        }
                        else if (finfo[0].Trim().ToLower() == "python")
                        {
                            string f = finfo[1].Trim().Replace("\\", "/");
                            if (System.IO.File.Exists(f))
                            {
                                exepy = f;
                            }
                        }
                    }
                }
            }
            if (!System.IO.File.Exists(exeffpy))
            {
                if (System.IO.File.Exists("C:/Program Files (x86)/FontForgeBuilds/bin/ffpython.exe"))
                {
                    exeffpy = "C:/Program Files (x86)/FontForgeBuilds/bin/ffpython.exe";
                }
                else if (System.IO.File.Exists("C:/Program Files/FontForgeBuilds/bin/ffpython.exe"))
                {
                    exeffpy = "C:/Program Files/FontForgeBuilds/bin/ffpython.exe";
                }
            }
        }

        private void ButtonStart_Click(object sender, EventArgs e)
        {
            path = AppDomain.CurrentDomain.BaseDirectory;
            string filein = textBoxIn.Text.Trim();
            string filein2 = textBoxIn2.Text.Trim();
            fileout = textBoxOut.Text.Trim();
            isotcff = comboBoxApp.SelectedIndex == 0;
            string[] stmodes = { "st", "var", "sat", "faf", "jt", "ts", "st.twp.m" };
            string stmode = stmodes[comboBoxSys.SelectedIndex];
            bool ffset = false;
            if (!isotcff)
            {
                ffset = true;
            }
            if (stmode == "st")
            {
                if (comboBoxVar.SelectedIndex == 0)
                {
                    stmode += ".dft";
                }
                else if (comboBoxVar.SelectedIndex == 1)
                {
                    stmode += ".tw";
                }
                else if (comboBoxVar.SelectedIndex == 2)
                {
                    stmode += ".hk";
                }
                else if (comboBoxVar.SelectedIndex == 3)
                {
                    stmode += ".cl";
                }
                if (comboBoxMulti.SelectedIndex == 0)
                {
                    stmode += ".n";
                }
                else if (comboBoxMulti.SelectedIndex == 1)
                {
                    stmode += ".s";
                }
                else if (comboBoxMulti.SelectedIndex == 2)
                {
                    stmode += ".m";
                }
            }
            SetExec();
            if ((!System.IO.File.Exists(filein)) || (!System.IO.File.Exists(filein2) && (stmode == "sat" || stmode == "faf")) || string.IsNullOrWhiteSpace(fileout))
            {
                MessageBox.Show(this, "文件無效，請重新選擇。", "提示", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }
            if (isotcff && !System.IO.File.Exists(exepy))
            {
                if (System.IO.File.Exists(exeffpy))
                {
                    if (MessageBox.Show(this, "未能找到 Python,要使用 FontForge 所附帶的 Python 模塊嗎？可以在 appdata 文件中設置 python.exe 的路徑。", "提示", MessageBoxButtons.YesNo, MessageBoxIcon.Question, MessageBoxDefaultButton.Button1) == DialogResult.Yes)
                    {
                        exepy = exeffpy;
                        ffset = true;
                    }
                    else
                    {
                        return;
                    }
                }
                else
                {
                    MessageBox.Show(this, "未能找到 Python 或 FontForge,請在 appdata 文件中設置 python.exe 或 fontforge.exe 的路徑。", "提示", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return;
                }
            }

            if (!isotcff && !System.IO.File.Exists(exeffpy))
            {
                MessageBox.Show(this, "未能找到 FontForge,請在 appdata 文件中設置 fontforge.exe 的路徑。", "提示", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }
            if (checkBoxInfo.Checked && string.IsNullOrWhiteSpace(textBoxName.Text))
            {
                MessageBox.Show(this, "您需要輸入字體名稱。", "提示", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }
            if (stmode == "sat" || stmode == "faf")
            {
                filein = $"-i \"{filein}\" -i2 \"{filein2}\"";
            }
            else
            {
                filein = $"-i \"{filein}\"";
            }
            string pyfile = isotcff ? path + "converto.py" : path + "convertf.py";
            pyfile = pyfile.Replace('\\', '/');
            string args = $"\"{pyfile}\" {filein} -o \"{fileout}\" -wk {stmode}";
            if (stmode != "var" && checkBoxYitizi.Checked)
            {
                args += " -v";
            }
            if (checkBoxInfo.Checked && !string.IsNullOrWhiteSpace(textBoxName.Text))
            {
                args += $" -n \"{textBoxName.Text}\"";
                if (!string.IsNullOrWhiteSpace(textBoxTCName.Text))
                {
                    args += $" -ntc \"{textBoxTCName.Text}\"";
                }
                if (!string.IsNullOrWhiteSpace(textBoxSCName.Text))
                {
                    args += $" -nsc \"{textBoxSCName.Text}\"";
                }
                if (!string.IsNullOrWhiteSpace(textBoxVersi.Text))
                {
                    args += $" -vn \"{textBoxVersi.Text}\"";
                }
            }
            string ffpath = "";
            if (ffset)
            {
                string bin = exeffpy.Substring(0, exeffpy.LastIndexOf('/'));
                ffpath = bin.Substring(0, bin.LastIndexOf('/'));
            }
            cmdline = ffset ? $"set \"PYTHONHOME={ffpath}\"&\"{exeffpy}\" {args}" : $"\"{exepy}\" {args}";
            if (!showCMD)
            {
                cmdline += "&exit";
            }
            panelMain.Enabled = false;
            Cursor = Cursors.WaitCursor;
            Text = "正在处理...";
            err = "";
            outinfo = "";
            thRun = new System.Threading.Thread(ThRun);
            thRun.IsBackground = true;
            thRun.Start();
        }

        private void ThRun()
        {
            using (System.Diagnostics.Process p = new System.Diagnostics.Process())
            {
                p.StartInfo.FileName = "cmd";
                fileout = fileout.Replace('\\', '/');
                p.StartInfo.UseShellExecute = false;
                p.StartInfo.CreateNoWindow = !showCMD;
                p.StartInfo.RedirectStandardError = !showCMD;
                p.StartInfo.RedirectStandardOutput = !showCMD;
                p.StartInfo.RedirectStandardInput = true;
                p.Start();
                p.StandardInput.WriteLine(cmdline);
                if (!showCMD)
                {
                    p.ErrorDataReceived += P_ErrorDataReceived;
                    p.OutputDataReceived += P_OutputDataReceived;
                    p.BeginErrorReadLine();
                    p.BeginOutputReadLine();
                }
                p.WaitForExit();
                p.Close();
            }
            Invoke(new Action(delegate
            {
                panelMain.Enabled = true;
                Cursor = Cursors.Default;
                Text = " 中文字體簡繁處理工具";
                if (System.IO.File.Exists(fileout))
                {
                    if (outinfo.EndsWith("Finished!"))
                    {
                        if (string.IsNullOrWhiteSpace(err))
                        {
                            MessageBox.Show(this, "成功！", "提示", MessageBoxButtons.OK, MessageBoxIcon.Information);
                        }
                        else
                        {
                            MessageBox.Show(this, "错误！\r\n" + err, "提示", MessageBoxButtons.OK, MessageBoxIcon.Error);
                        }
                    }
                    else if (!string.IsNullOrWhiteSpace(err))
                    {
                        MessageBox.Show(this, "失败！\r\n" + err, "提示", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                    else
                    {
                        MessageBox.Show(this, "处理完毕，但无法确定是否成功。", "提示", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                }
                else
                {
                    MessageBox.Show(this, "失败！\r\n" + err, "提示", MessageBoxButtons.OK, MessageBoxIcon.Error);

                }
            }));
        }

        private void P_OutputDataReceived(object sender, System.Diagnostics.DataReceivedEventArgs e)
        {
            if (!string.IsNullOrWhiteSpace(e.Data))
            {
                outinfo = e.Data;
            }
        }

        private void P_ErrorDataReceived(object sender, System.Diagnostics.DataReceivedEventArgs e)
        {
            if (!string.IsNullOrWhiteSpace(e.Data) && (e.Data.Contains("Error") || e.Data.Contains("ERROR") || e.Data.Contains("[Errno")) && !e.Data.Contains("raise"))
            {
                err += e.Data + "\r\n";
            }
        }

        private void FormMain_FormClosing(object sender, FormClosingEventArgs e)
        {
            if (thRun != null && thRun.IsAlive)
            {
                e.Cancel = true;
                //if (MessageBox.Show("有任務正在工作，確定要放棄當前任務嗎？", "提示", MessageBoxButtons.YesNo, MessageBoxIcon.Exclamation, MessageBoxDefaultButton.Button2) == DialogResult.Yes)
                //{
                //    Environment.Exit(0);
                //}
                //else
                //{
                //    e.Cancel = true;
                //}
            }
        }
        private void CheckBoxInfo_CheckedChanged(object sender, EventArgs e) => panel1.Enabled = checkBoxInfo.Checked;
        private void TextBox_DragEnter(object sender, DragEventArgs e) => e.Effect = e.Data.GetDataPresent(DataFormats.FileDrop) ? DragDropEffects.All : DragDropEffects.None;
        private void TextBox_DragDrop(object sender, DragEventArgs e) => ((TextBox)sender).Text = ((System.Array)e.Data.GetData(DataFormats.FileDrop)).GetValue(0).ToString();

        private void ComboBoxSys_SelectedIndexChanged(object sender, EventArgs e)
        {
            checkBoxYitizi.Enabled = comboBoxSys.SelectedIndex != 1;
            panelTC.Enabled = comboBoxSys.SelectedIndex == 0;
            labeli2.Enabled = comboBoxSys.SelectedIndex == 2 || comboBoxSys.SelectedIndex == 3;
            textBoxIn2.Enabled = comboBoxSys.SelectedIndex == 2 || comboBoxSys.SelectedIndex == 3;
            linkLabelIn2.Enabled = comboBoxSys.SelectedIndex == 2 || comboBoxSys.SelectedIndex == 3;
        }

        private void LinkLabelIn_LinkClicked(object sender, LinkLabelLinkClickedEventArgs e)
        {
            if (openFileDialog1.ShowDialog() == DialogResult.OK)
            {
                textBoxIn.Text = openFileDialog1.FileName;
            }
        }

        private void LinkLabelIn2_LinkClicked(object sender, LinkLabelLinkClickedEventArgs e)
        {
            if (openFileDialog1.ShowDialog() == DialogResult.OK)
            {
                textBoxIn2.Text = openFileDialog1.FileName;
            }
        }

        private void LinkLabelOut_LinkClicked(object sender, LinkLabelLinkClickedEventArgs e)
        {
            if (saveFileDialog1.ShowDialog() == DialogResult.OK)
            {
                textBoxOut.Text = saveFileDialog1.FileName;
            }
        }

        private void LinkLabel1_LinkClicked(object sender, LinkLabelLinkClickedEventArgs e)
        {
            System.Diagnostics.Process.Start("https://github.com/GuiWonder/TCFontCreator");
        }
    }
}
