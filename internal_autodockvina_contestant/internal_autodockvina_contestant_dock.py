#!/usr/bin/env python

__author__ = 'j5wagner@ucsd.edu'


from d3r.celppade.custom_dock import Dock

class autodockvina(Dock):
    """Abstract class defining methods for a custom docking solution
    for CELPP
    """
    Dock.SCI_PREPPED_LIG_SUFFIX = '_prepared.pdbqt'
    Dock.SCI_PREPPED_PROT_SUFFIX = '_prepared.pdbqt'


    def ligand_technical_prep(self, sci_prepped_lig, targ_info_dict = {}):
        """
        'Technical preparation' is the step immediate preceding
        docking. During this step, you may perform any file
        conversions or processing that are specific to your docking
        program. Implementation of this function is optional.
        :param sci_prepped_lig: Scientifically prepared ligand file
        :param targ_info_dict: A dictionary of information about this target and the candidates chosen for docking.
        :returns: A list of result files to be copied into the
        subsequent docking folder. The base implementation merely
        returns the input string in a list (ie. [sci_prepped_lig]) 
        """
        return super(autodockvina,
                     self).ligand_technical_prep(sci_prepped_lig,
                                                 targ_info_dict = targ_info_dict)

    def receptor_technical_prep(self, 
                                sci_prepped_receptor, 
                                pocket_center, 
                                targ_info_dict = {}):
        """
        'Technical preparation' is the step immediately preceding
        docking. During this step, you may perform any file
        conversions or processing that are specific to your docking
        program. Implementation of this function is optional.
        :param sci_prepped_receptor: Scientifically prepared receptor file
        :param pocket_center: list of floats [x,y,z] of predicted pocket center
        :param targ_info_dict: A dictionary of information about this target and the candidates chosen for docking.
        :returns: A list of result files to be copied into the
        subsequent docking folder. This implementation merely
        returns the input string in a list (ie [sci_prepped_receptor])
        """
        
        #return [sci_prepped_receptor, pocket_center]
        return super(autodockvina,
                     self).receptor_technical_prep(sci_prepped_receptor, 
                                                   pocket_center,
                                                   targ_info_dict=targ_info_dict)




    def dock(self, 
             tech_prepped_lig_list, 
             tech_prepped_receptor_list, 
             output_receptor_pdb, 
             output_lig_mol, 
             targ_info_dict={}):
        """
        This function is the only one which the contestant MUST
        implement.  The dock() step runs the actual docking
        algorithm. Its first two arguments are the return values from
        the technical preparation functions for the ligand and
        receptor. These arguments are lists of file names (strings),
        which can be assumed to be in the current directory. 
        If prepare_ligand() and ligand_technical_prep() are not
        implemented by the contestant, tech_prepped_lig_list will
        contain a single string which names a SMILES file in the
        current directory.
        If receptor_scientific_prep() and receptor_technical_prep() are not
        implemented by the contestant, tech_prepped_receptor_list will
        contain a single string which names a PDB file in the current
        directory.
        The outputs from this step must be two files - a pdb with the
        filename specified in the output_receptor_pdb argument, and a
        mol with the filename specified in the output_ligand_mol
        argument.
        :param tech_prepped_lig_list: The list of file names resturned by ligand_technical_prep. These have been copied into the current directory.
        :param tech_prepped_receptor_list: The list of file names resturned by receptor_technical_prep. These have been copied into the current directory.
        :param output_receptor_pdb: The final receptor (after docking) must be converted to pdb format and have exactly this file name.
        :param output_lig mol: The final ligand (after docking) must be converted to mol format and have exactly this file name.
        :param targ_info_dict: A dictionary of information about this target and the candidates chosen for docking.
        :returns: True if docking is successful, False otherwise. Unless overwritten, this implementation always returns False
        """
        receptor_pdbqt = tech_prepped_receptor_list[0]
        ligand_pdbqt = tech_prepped_lig_list[0]
        pocket_center = targ_info_dict['pocket_center']
        
        vina_command = ('vina --receptor ' + receptor_pdbqt + '  --ligand  ' +
                         ligand_pdbqt + ' --center_x ' + str(pocket_center[0]) +
                        ' --center_y ' + str(pocket_center[1]) +
                        ' --center_z ' + str(pocket_center[2]) +
                        ' --size_x 15 --size_y 15 --size_z 15 --seed 999 ' +
                        ' >& vina_output')
        print "Running: " + vina_command
        os.system(vina_command)

        out_dock_file = ligand_pdbqt.replace('.pdbqt','_out.pdbqt')


        ## Convert the receptor to pdb
        #intermediates_prefix = 'postdocking'
        #output_prefix = '%s_docked' %(candidate_prefix)
        #receptorPdbqt = out_dock_file.replace('ligand_out',candidate_name)
        #receptorPdbqt = candidate_prefix+'.pdbqt'
        ## This receptor pdb will be one of our final outputs
        #outputReceptorPdb = "%s.pdb" %(output_prefix)
        os.system('. /usr/local/mgltools/bin/mglenv.sh; python $MGL_ROOT/MGLToolsPckgs/AutoDockTools/Utilities24/pdbqt_to_pdb.py -f %s -o %s' %(receptor_pdbqt, output_receptor_pdb))

        ## Then make the ligand mol
        ## pdbqt_to_pdb.py can't split up the multiple poses in vina's output files, so we do that by hand
        with open(out_dock_file) as fo:
            fileData = fo.read()
        fileDataSp = fileData.split('ENDMDL')

        ## Write out each pose to its own pdb and mol file, then merge with the receptor to make the complex files.
        for index, poseText in enumerate(fileDataSp[:-1]):
            this_pose_pdbqt = 'ligand_pose'+str(index+1)+'.pdbqt'
            this_pose_pdb = 'ligand_pose'+str(index+1)+'.pdb'
            this_pose_mol = 'ligand_pose'+str(index+1)+'.mol'
            with open(this_pose_pdbqt,'wb') as wf:
                wf.write(poseText+'ENDMDL')
            os.system('. /usr/local/mgltools/bin/mglenv.sh; python $MGL_ROOT/MGLToolsPckgs/AutoDockTools/Utilities24/pdbqt_to_pdb.py -f ' + this_pose_pdbqt + ' -o '+ this_pose_pdb)
            os.system('babel -ipdb ' +this_pose_pdb + ' -omol ' + this_pose_mol)

        ## Here convert our top-ranked pose to the final submission for this docking
        ## Right now we're ignoring everything other than the top pose
        top_intermediate_mol = 'ligand_pose1.mol'
        os.system('cp ligand_pose1.mol ' + output_lig_mol)

        #return super(autodockvina, 
        #             self).dock(tech_prepped_lig_list,
        #                        tech_prepped_receptor_list,
        #                        output_receptor_pdb, 
        #                        output_lig_mol,
        #                        targ_info_dict=targ_info_dict)





if ("__main__") == (__name__):
    import os
    import logging
    import shutil
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-l", "--ligsciprepdir", metavar="PATH", help = "PATH where we can find the scientific ligand prep output")
    parser.add_argument("-p", "--protsciprepdir", metavar="PATH", help = "PATH where we can find the scientific protein prep output")
    parser.add_argument("-o", "--outdir", metavar = "PATH", help = "PATH where we will put the docking output")
    # Leave option for custom logging config here
    logger = logging.getLogger()
    logging.basicConfig( format  = '%(asctime)s: %(message)s', datefmt = '%m/%d/%y %I:%M:%S', filename = 'final.log', filemode = 'w', level   = logging.INFO )
    opt = parser.parse_args()
    lig_sci_prep_dir = opt.ligsciprepdir
    prot_sci_prep_dir = opt.protsciprepdir
    dock_dir = opt.outdir
    #running under this dir
    abs_running_dir = os.getcwd()
    log_file_path = os.path.join(abs_running_dir, 'final.log')
    log_file_dest = os.path.join(os.path.abspath(dock_dir), 'final.log')
    docker = autodockvina()
    docker.run_dock(prot_sci_prep_dir,
                    lig_sci_prep_dir,
                    dock_dir)
    #move the final log file to the result dir
    shutil.move(log_file_path, log_file_dest)
