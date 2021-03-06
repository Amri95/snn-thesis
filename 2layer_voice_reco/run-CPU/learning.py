

####################################################### README ####################################################################

# This is the main file which calls all the functions and trains the network by updating weights


#####################################################################################################################################

import numpy as np
from neuron import neuron
import random
from matplotlib import pyplot as plt
from spike_train import encode
from rl import rl
from rl import update
from parameters import param as par
from var_th import threshold

from console_write import *
from get_current_directory import *
from get_logmelspectrum import get_log_melspectrum
from wav_split import *
from record_synapse import *


def learning(learning_path, synapse):
	#potentials of output neurons
	potential_lists = []
	for i in range(par.kSecondLayerNuerons_):
		potential_lists.append([])

	#time series
	time_array  = np.arange(1, par.kTime_+1, 1)

	layer2 = []

	# creating the hidden layer of neurons
	for i in range(par.kSecondLayerNuerons_):
		a = neuron()
		layer2.append(a)

	for epoch in range(1):
		for wave_file in learning_path:
		#for wave_file in ["sounddata\F1\F1SYB01_が.wav"]:
			resemble_print(str(wave_file) + "  " + str(epoch))

			#音声データの読み込み
			splited_sig_array, samplerate = wav_split(str(wave_file))
			resemble_print(str(wave_file))

			splited_sig_array = remove_silence(splited_sig_array)
			print(len(splited_sig_array))
			#スパイクの連結
			#spike_train = wav_split2spike(splited_sig_array, samplerate)
			#spike_connected = np.array(connect_spike(spike_train))
			#for spike_train in spike_connected:
			for signal in splited_sig_array:
				#Generating melspectrum
				f_centers, mel_spectrum = get_log_melspectrum(signal, samplerate)

				#Generating spike train
				spike_train = np.array(encode(np.log10(mel_spectrum)))

				#calculating threshold value for the image
				var_threshold = threshold(spike_train)

				# resemble_print var_threshold
				# synapse_act = np.zeros((par.kSecondLayerNuerons_,par.kFirstLayerNuerons_))
				# var_threshold = 9
				# resemble_print var_threshold
				# var_D = (var_threshold*3)*0.07

				var_D = 0.15 * par.kScale_

				for x in layer2:
					x.initial(var_threshold)

				#flag for lateral inhibition
				flag_spike = 0

				img_win = 100

				active_potential = []
				for index1 in range(par.kSecondLayerNuerons_):
					active_potential.append(0)

				#Leaky integrate and fire neuron dynamics
				for time in time_array:
					for second_layer_position, second_layer_neuron in enumerate(layer2):
						active = []
						if(second_layer_neuron.t_rest < time):
							second_layer_neuron.P = (second_layer_neuron.P
													+ np.dot(
														synapse[second_layer_position], spike_train[:, time]
														)
													)
							#resemble_print("synapse : " + str(synapse[second_layer_position]))
							if(second_layer_neuron.P > par.kPrest_):
								second_layer_neuron.P -= var_D
							active_potential[second_layer_position] = second_layer_neuron.P

						potential_lists[second_layer_position].append(second_layer_neuron.P)

					# Lateral Inhibition
					if(flag_spike==0):
						max_potential = max(active_potential)
						if(max_potential > var_threshold):
							flag_spike = 1
							winner_neuron = np.argmax(active_potential)
							img_win = winner_neuron
							resemble_print("winner is " + str(winner_neuron))
							for s in range(par.kSecondLayerNuerons_):
								if(s != winner_neuron):
									layer2[s].P = par.kMinPotential_

					#Check for spikes and update weights
					for second_layer_position, second_layer_neuron in enumerate(layer2):
						neuron_status = second_layer_neuron.check()
						if(neuron_status == 1):
							second_layer_neuron.t_rest = time + second_layer_neuron.t_ref
							second_layer_neuron.P = par.kPrest_
							for first_layer_position in range(par.kFirstLayerNuerons_):
								#前シナプスの計算
								for back_time in range(-2, par.kTimeBack_-1, -1): #-2 → -20
									if 0 <= time + back_time < par.kTime_ + 1:
										if spike_train[first_layer_position][time + back_time] == 1:
											# resemble_print "weight change by" + str(update(synapse[j][h], rl(t1)))
											synapse[second_layer_position][first_layer_position] = update(
												synapse[second_layer_position][first_layer_position], rl(back_time)
												)
											resemble_print("back : " + str(second_layer_position) + "-" + str(first_layer_position) + " : " + str(synapse[second_layer_position][first_layer_position]))
								#後シナプスの計算
								for fore_time in range(2, par.kTimeFore_+1, 1): # 2 → 20
									if 0 <= time + fore_time<par.kTime_+1:
										if spike_train[first_layer_position][time + fore_time] == 1:
											# resemble_print "weight change by" + str(update(synapse[j][h], rl(t1)))
											synapse[second_layer_position][first_layer_position] = update(
												synapse[second_layer_position][first_layer_position], rl(fore_time)
												)
											resemble_print("fron : " + str(second_layer_position) + "-" + str(first_layer_position) + " : " + str(synapse[second_layer_position][first_layer_position]))


				if(img_win!=100):
					for first_layer_position in range(par.kFirstLayerNuerons_):
						if sum(spike_train[first_layer_position]) == 0:
							synapse[img_win][first_layer_position] -= 0.06 * par.kScale_
							if(synapse[img_win][first_layer_position]<par.kMinWait_):
								synapse[img_win][first_layer_position] = par.kMinWait_

	return potential_lists, synapse, layer2


def wav_split2spike(splited_sig_array, samplerate):
	spike_train = []
	for signal in splited_sig_array:

		#Generating melspectrum
		f_centers, mel_spectrum = get_log_melspectrum(signal, samplerate)

		#Generating spike train
		spike_train.append(np.array(encode(10 * np.log10(mel_spectrum))))

	return spike_train


def connect_spike(spike_train):
	#頭を基に、後ろ4つのスパイクを連結
	spike_connected = []
	for i in range(0, len(spike_train) - 3, 2):
		spike_connected_wip = []
		spike_connected_wip.extend(spike_train[i])
		spike_connected_wip.extend(spike_train[i+1])
		spike_connected_wip.extend(spike_train[i+2])
		spike_connected_wip.extend(spike_train[i+3])
		spike_connected.append(spike_connected_wip)

	return spike_connected


def remove_silence(splited_sig_array):
    db_sum_list = [sum(abs(signal)) for signal in splited_sig_array]
    remove_index = []
    for index, db in enumerate(db_sum_list):
        if db < 1:
            remove_index.append(index)

    remove_index.reverse()
    for i in remove_index:
        splited_sig_array.pop(i)
    return splited_sig_array

if __name__ == "__main__":
	import random
	from get_current_directory import get_mappingfile_path
	from export_parameters import export_par
	from mapping import *
	from third_layer import *
	from color_map import export_color_map
	import os

	#学習
	#get wavefile path for learning
	learning_path = get_learningfile_path()
	#learning_path = get_mappingfile_path()
	#learning_path = [onedivision for a in learning_path for onedivision in a] #2次元のパスを1次元に変更

	#which synapse
	args = sys.argv
	if len(args) == 1:
		#synapse matrix	initialization
		synapse = np.zeros((par.kSecondLayerNuerons_, par.kFirstLayerNuerons_))
		for i in range(par.kSecondLayerNuerons_):
			for j in range(par.kFirstLayerNuerons_):
				synapse[i][j] = random.uniform(0.4, 0.5 * par.kScale_)
	else:
		input_synaps = args[1]
		synapse = import_synapse("synapse_record/" + str(input_synaps) + ".txt")
		#synapse = import_synapse(input_synaps + "/" + input_synaps +".txt")


	run_time = create_timestamp()
	os.mkdir(run_time)
	initial_synapse_path = run_time + "/initial" + run_time
	print(initial_synapse_path)
	export_list2txt(synapse, initial_synapse_path)

	export_par(run_time + "/run_parameters")

	potential_lists, synapse, layer2 = learning(learning_path, synapse)

	learned_synapse_path = run_time + "/1-2synapse" + run_time
	print("export : " + learned_synapse_path)
	export_list2txt(synapse, learned_synapse_path)

	#2,3層目の学習
	secondhand_wav_file = []
	speaker_list = [i for i in range(0, 12)]

	mapping_list = [[] for _ in range(par.kSecondLayerNuerons_)]

	mapping_path = get_mappingfile_path()
	for i in range(len(mapping_path)):
		mapping_path[i].sort()

	second_third_synapse = np.zeros(par.kSecondLayerNuerons_)
	third_neuron = []
	mapping_list = []

	for syllable_num in range(len(mapping_path[0])):
		use_speakers = random.sample(speaker_list, 6)
		resemble_print(use_speakers)
		secondhand_wav_file.append(use_speakers)
		winner_neurons = []
		for speaker in use_speakers:
			resemble_print(str(speaker) + " : " + str(syllable_num) + " : " + str(mapping_path[speaker][syllable_num]))
			resemble_print(str(speaker) + " : " + str(syllable_num) + " : " + str(mapping_path[speaker][syllable_num]))
			count_neuron_fire = winner_take_all(synapse, mapping_path[speaker][syllable_num])
			num_neuron_fire = sum(count_neuron_fire)
			print(num_neuron_fire)

			second_third_synapse += count_neuron_fire / num_neuron_fire

		second_third_synapse = second_third_synapse / len(use_speakers)
		print(second_third_synapse)
		third_neuron.append(second_third_synapse)
		mapping_list.append(extract_label(mapping_path[speaker][syllable_num]))

	second_third_synapse_path = run_time + "/2-3synapse" + run_time
	export_list2txt(third_neuron, second_third_synapse_path)

	#対応付け
	third_neuron = []
	mapping_list = []
	neuron_parsent = np.zeros((len(mapping_path[0]),len(mapping_path[0])))
	win_neuron = np.zeros(len(mapping_path[0]))
	accuracy = np.zeros((len(mapping_path[0]),len(mapping_path[0])))

	for syllable_num in range(len(mapping_path[0])): #単音節の数(F1のファイル数)分ループ
		use_speakers = random.sample(speaker_list, 6)
		resemble_print(use_speakers)
		secondhand_wav_file.append(use_speakers)
		winner_neurons = []

		mapping_list.append(extract_label(mapping_path[0][syllable_num]))

		for speaker in use_speakers:
			resemble_print(str(speaker) + " : " + str(syllable_num) + " : " + str(mapping_path[speaker][syllable_num]))
			count_neuron_fire = winner_take_all(synapse, mapping_path[speaker][syllable_num])
			num_neuron_fire = sum(count_neuron_fire)

			parsent_neuron_fire = count_neuron_fire / num_neuron_fire

			#最も近いニューロンに1を加算する
			for syllable in range(len(mapping_path[0])):
				print(second_third_synapse[syllable])
				how_like = cos_sim(second_third_synapse[syllable], parsent_neuron_fire)
				#print(how_like)
				neuron_parsent[syllable_num][syllable] += how_like
				win_neuron[syllable] += how_like
			#print(win_neuron)
			#print(max_index(win_neuron))
			accuracy[syllable_num][max_index(win_neuron)] += 1

	#neuron_parsent = neuron_parsent / len(use_speakers)
	print(neuron_parsent)
	accuracy = accuracy / len(use_speakers)
	export_list2txt(neuron_parsent, run_time + "/end" + run_time)
	export_list2txt(accuracy, run_time + "/answer" + run_time)

	#全体の正答率の算出
	corrent_answers = []
	for i in range(len(mapping_path[0])):
		print(mapping_list[i] + " : " + str(accuracy[i][i]))
		corrent_answers.append(accuracy[i][i])
	
	print(sum(corrent_answers) / len(mapping_path[0]))

	export_color_map(accuracy, run_time + "/color_map" +run_time)
