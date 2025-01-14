import numpy as np
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
import os

import sys
sys.path.append('..')
import platform

# if platform.system()=='Windows':
#     from importlib import reload
# else:
#     reload(sys)
#     sys.setdefaultencoding('utf8')


from Utilities.utils import image_show
import random as rnd
import time
import multiprocessing as multi_thread
print_separator = "#################################################################"
from tensorflow.python.client import device_lib
import copy as cpy
import scipy.misc as misc

STANDARD_GRAYSCALE_THRESHOLD_VALUE = 240
ALTERNATE_GRAYSCALE_LOW=170
ALTERNATE_GRAYSCALE_HGH=250

# data_reading_mode = 'Full'
data_reading_mode = 'Partial'

LABEL_LENGTH=6
MaxStyleReferenceLossNum=16
ContentInputNumberActual=0
printInfoSec=15
displayStyleNum = 8


GRAYSCALE_AVG = 127.5
class Dataset(object):
    def __init__(self,
                 data_list,
                 label0_list,label1_list,
                 sorted_by_label0,
                #  print_marks,
                 info_print_interval):
        self.data_list = data_list
        self.label0_list = label0_list
        self.label1_list = label1_list

        if sorted_by_label0:
            self.sorted_data_by_label0(info_print_interval=info_print_interval)




    def sorted_data_by_label0(self,info_print_interval):
        print(print_separator)
        label0_vec = np.unique(self.label0_list)
        sorted_data_list=list()
        sorted_label0_list = list()
        sorted_label1_list = list()



        sort_start = time.time()
        counter=0
        for label0 in label0_vec:
            found_indices = [ii for ii in range(len(self.label0_list)) if self.label0_list[ii] == label0]
            for ii in found_indices:
                sorted_data_list.append(self.data_list[ii])
                sorted_label0_list.append(self.label0_list[ii])
                sorted_label1_list.append(self.label1_list[ii])

            print('SortingForLabel0:%d/%d' % (counter+1, len(label0_vec)), end="\r")
            if time.time()-sort_start > info_print_interval or label0==label0_vec[0] or counter == len(label0_vec)-1:
                print('SortingForLabel0:%d/%d' % (counter+1, len(label0_vec)))
                sort_start=time.time()
            counter+=1
        self.data_list = sorted_data_list
        self.label0_list = sorted_label0_list
        self.label1_list = sorted_label1_list
        print(print_separator)



class Dataset_Iterator(object):
    def __init__(self,config, thread_num,
                 true_style,
                 style_reference_list,content_prototype_list,
                 content_input_number_actual,
                 ):

        self.config=config
        self.true_style = true_style
        self.style_reference_list = style_reference_list

        self.thread_num = thread_num
        self.content_input_num = len(content_prototype_list)
        self.content_input_number_actual=content_input_number_actual

        self.label0_vec=config.datasetConfig.loadedLabel0Vec
        self.label1_vec=config.datasetConfig.loadedLabel1Vec

        self.content_data_list_alignment_with_true_style_data(content_prototype_list=content_prototype_list)




    def content_data_list_alignment_with_true_style_data(self, content_prototype_list):

        find_start = time.time()
        label0_counter = 0
        content_data_list = list()
        content_label0_list = list()
        content_label1_list = list()
        for ii in range(len(content_prototype_list)):
            content_data_list.append(cpy.deepcopy(self.true_style.data_list))
            content_label0_list.append(cpy.deepcopy(self.true_style.label0_list))
            content_label1_list.append(cpy.deepcopy(self.true_style.label1_list))

        label0_vec = np.unique(self.true_style.label0_list)
        delete_label_add = 0
        delete_data_add = 0
        print(print_separator)
        for label0 in label0_vec:
            current_label0_indices_on_the_style_data = [ii for ii in range(len(self.true_style.label0_list)) if self.true_style.label0_list[ii] == label0]

            valid_label0 = True
            for kk in range(len(content_prototype_list)):
                if not label0 in content_prototype_list[kk].label0_list:
                    valid_label0 = False
                    break
            if not valid_label0:
                delete_label_add += 1
                delete_data_add += len(current_label0_indices_on_the_style_data)
                delete_counter = 0
                current_label0_indices_on_the_style_data.sort()
                for iii in current_label0_indices_on_the_style_data:
                    del self.true_style.label0_list[iii-delete_counter]
                    del self.true_style.label1_list[iii-delete_counter]
                    del self.true_style.data_list[iii-delete_counter]
                    for jjj in range(len(self.style_reference_list)):
                        del self.style_reference_list[jjj].label0_list[iii-delete_counter]
                        del self.style_reference_list[jjj].label1_list[iii-delete_counter]
                        del self.style_reference_list[jjj].data_list[iii-delete_counter]
                    # for jjj in range(len(self.loss_style_reference_list)):
                    #     del self.loss_style_reference_list[jjj].label0_list[iii - delete_counter]
                    #     del self.loss_style_reference_list[jjj].label1_list[iii - delete_counter]
                    #     del self.loss_style_reference_list[jjj].data_list[iii - delete_counter]
                    for jjj in range(len(content_prototype_list)):
                        del content_data_list[jjj][iii - delete_counter]
                        del content_label0_list[jjj][iii - delete_counter]
                        del content_label1_list[jjj][iii - delete_counter]
                    delete_counter += 1

                continue
            else:
                current_label0_indices_on_the_style_data = [ii for ii in range(len(self.true_style.label0_list)) if self.true_style.label0_list[ii] == label0]
                for ii in range(len(content_prototype_list)):
                    current_prototype_dataset = content_prototype_list[ii]
                    current_label0_index_on_the_content_prototype_data = current_prototype_dataset.label0_list.index(label0)
                    for jj in current_label0_indices_on_the_style_data:
                        content_data_list[ii][jj] = current_prototype_dataset.data_list[current_label0_index_on_the_content_prototype_data]
                        content_label0_list[ii][jj] = current_prototype_dataset.label0_list[current_label0_index_on_the_content_prototype_data]
                        content_label1_list[ii][jj] = current_prototype_dataset.label1_list[current_label0_index_on_the_content_prototype_data]


                print('FindingCorrespondendingContentPrototype_BasedOnLabel0: %d/%d, ' %
                          (label0_counter + 1, len(label0_vec)), end='')
                print('Deleted %d Label0s with %d samples' %
                          (delete_label_add, delete_data_add), end="\r")
                
                if time.time() - find_start > printInfoSec or label0 == label0_vec[0] or label0_counter == len(label0_vec) - 1:
                    print('FindingCorrespondendingContentPrototype_BasedOnLabel0: %d/%d, ' %
                          (label0_counter + 1, len(label0_vec)), end='')
                    print('Deleted %d Label0s with %d samples' %
                          (delete_label_add, delete_data_add))
                    find_start = time.time()
            label0_counter += 1


        self.content_prototype_list = content_prototype_list
        for ii in range(len(content_prototype_list)):
            self.content_prototype_list[ii].data_list = content_data_list[ii]
            self.content_prototype_list[ii].label0_list = content_label0_list[ii]
            self.content_prototype_list[ii].label1_list = content_label1_list[ii]



    def reproduce_dataset_lists(self, info, shuffle,info_print_interval):
        if shuffle:
            old_content_prototype_list = cpy.deepcopy(self.content_prototype_list)
            old_true_style_data_list = self.true_style.data_list
            old_true_style_label0_list = self.true_style.label0_list
            old_true_style_label1_list = self.true_style.label1_list

            self.true_style.data_list=list()
            self.true_style.label0_list=list()
            self.true_style.label1_list=list()
            for ii in range(self.content_input_num):
                self.content_prototype_list[ii].data_list = list()
                self.content_prototype_list[ii].label0_list = list()
                self.content_prototype_list[ii].label1_list = list()

            indices_shuffled = np.random.permutation(len(old_true_style_data_list))
            for ii in indices_shuffled:
                self.true_style.data_list.append(old_true_style_data_list[ii])
                self.true_style.label0_list.append(old_true_style_label0_list[ii])
                self.true_style.label1_list.append(old_true_style_label1_list[ii])
                for jj in range(self.content_input_num):
                    self.content_prototype_list[jj].data_list.append(old_content_prototype_list[jj].data_list[ii])
                    self.content_prototype_list[jj].label0_list.append(old_content_prototype_list[jj].label0_list[ii])
                    self.content_prototype_list[jj].label1_list.append(old_content_prototype_list[jj].label1_list[ii])

        time_start = time.time()
        label1_vec = np.unique(self.true_style.label1_list)
        label1_counter = 0
        for label1 in label1_vec:
            found_indices = [ii for ii in range(len(self.true_style.label1_list)) if self.true_style.label1_list[ii] == label1]
            for jj in range(self.config.datasetConfig.displayStyleNum):
                current_new_indices = rnd.sample(found_indices, len(found_indices))
                for kk in range(len(found_indices)):
                    self.style_reference_list[jj].data_list[found_indices[kk]] = \
                        self.true_style.data_list[current_new_indices[kk]]
                    self.style_reference_list[jj].label0_list[found_indices[kk]] = \
                        self.true_style.label0_list[current_new_indices[kk]]
                    self.style_reference_list[jj].label1_list[found_indices[kk]] = \
                        self.true_style.label1_list[current_new_indices[kk]]

            # for jj in range(len(self.loss_style_reference_list)):
            #     current_new_indices = rnd.sample(found_indices, len(found_indices))
            #     for kk in range(len(found_indices)):
            #         self.loss_style_reference_list[jj].data_list[found_indices[kk]] = \
            #             self.true_style.data_list[current_new_indices[kk]]
            #         self.loss_style_reference_list[jj].label0_list[found_indices[kk]] = \
            #             self.true_style.label0_list[current_new_indices[kk]]
            #         self.loss_style_reference_list[jj].label1_list[found_indices[kk]] = \
            #             self.true_style.label1_list[current_new_indices[kk]]

            label1_counter += 1
            print('%s:DatasetReInitialization@CurrentLabel1:%d/%d(Label1:%s);' % (info, label1_counter, len(label1_vec), label1), end="\r")
            if time.time() - time_start > info_print_interval or label1_counter == len(label1_vec) or label1_counter == 1:
                time_start = time.time()
                print('%s:DatasetReInitialization@CurrentLabel1:%d/%d(Label1:%s);' % (info, label1_counter, len(label1_vec), label1))




    def iterator_reset(self,sess):
        sess.run(self.true_style_iterator.initializer,
                 feed_dict={self.true_style_data_list_input_op:self.true_style.data_list,
                            self.true_style_label0_list_input_op:self.true_style.label0_list,
                            self.true_style_label1_list_input_op:self.true_style.label1_list})
        for ii in range(self.content_input_num):
            sess.run(self.prototype_iterator_list[ii].initializer,
                     feed_dict={self.prototype_data_list_input_op_list[ii]:self.content_prototype_list[ii].data_list,
                                self.prototype_label0_list_input_op_list[ii]:self.content_prototype_list[ii].label0_list,
                                self.prototype_label1_list_input_op_list[ii]:self.content_prototype_list[ii].label1_list})
        for ii in range(self.config.datasetConfig.displayStyleNum):
            sess.run(self.reference_iterator_list[ii].initializer,
                     feed_dict={self.reference_data_list_input_op_list[ii]: self.style_reference_list[ii].data_list,
                                self.reference_label0_list_input_op_list[ii]: self.style_reference_list[ii].label0_list,
                                self.reference_label1_list_input_op_list[ii]: self.style_reference_list[ii].label1_list})
        # for ii in range(len(self.loss_style_reference_list)):
        #     sess.run(self.loss_reference_iterator_list[ii].initializer,
        #              feed_dict={self.loss_reference_data_list_input_op_list[ii]: self.loss_style_reference_list[ii].data_list,
        #                         self.loss_reference_label0_list_input_op_list[ii]: self.loss_style_reference_list[ii].label0_list,
        #                         self.loss_reference_label1_list_input_op_list[ii]: self.loss_style_reference_list[
        #                             ii].label1_list})


    def create_dataset_op(self, discrminator_label1_vec, augmentation):
        def _get_tensor_slice():
            data_list_placeholder = tf.placeholder(dtype=tf.string, shape=[None])
            label0_list_placeholder = tf.placeholder(dtype=tf.string, shape=[None])
            label1_list_placeholder = tf.placeholder(dtype=tf.string, shape=[None])
            dataset_op = tf.data.Dataset.from_tensor_slices((data_list_placeholder,
                                                             label0_list_placeholder,
                                                             label1_list_placeholder))
            return dataset_op, \
                   data_list_placeholder, \
                   label0_list_placeholder, label1_list_placeholder



        def _parser_func(file_list,label0_list,label1_list):
            image_string = tf.read_file(file_list)
            image_decoded = tf.image.decode_image(contents=image_string, channels=1)
            image_resized = tf.image.resize_image_with_crop_or_pad(image_decoded, self.config.datasetConfig.imgWidth, self.config.datasetConfig.imgWidth)
            img_output = tf.slice(image_resized,
                                  [0, 0, 0],
                                  [self.config.datasetConfig.imgWidth, self.config.datasetConfig.imgWidth, self.config.datasetConfig.channels])
            return img_output, label0_list, label1_list



        def _convert_label_to_one_hot(dense_label,voc):
            # table = tf.contrib.lookup.index_table_from_tensor(mapping=voc, default_value=0)
            init = tf.lookup.KeyValueTensorInitializer(keys=voc, values=range(len(voc)))
            table = tf.lookup.StaticHashTable(init, default_value=0)
            encoded = tf.one_hot(table.lookup(dense_label),len(voc), dtype=tf.float32)
            return encoded

        def _random_thickness(input_tensor, fixed_mask):
            if fixed_mask:
                mask_tensor = STANDARD_GRAYSCALE_THRESHOLD_VALUE * \
                              tf.ones(shape=input_tensor.shape,
                                      dtype=input_tensor.dtype)
                threshold = mask_tensor
            else:
                threshold_v = tf.random_uniform(shape=[int(input_tensor.shape[0]), 1, 1, 1],
                                                minval=ALTERNATE_GRAYSCALE_LOW,
                                                maxval=ALTERNATE_GRAYSCALE_HGH,
                                                dtype=tf.float32)
                threshold = tf.tile(threshold_v, [1, int(input_tensor.shape[1]), int(input_tensor.shape[2]), 1])
                mask_tensor = tf.multiply(threshold,
                                          tf.ones(shape=input_tensor.shape,
                                                  dtype=input_tensor.dtype))

            condition = tf.greater_equal(input_tensor, mask_tensor)
            output_tensor = tf.where(condition,
                                     tf.ones_like(input_tensor),
                                     tf.zeros_like(input_tensor))
            return output_tensor, threshold





        # for true style image
        true_style_dataset, \
        true_style_data_list_input_op, \
        true_style_label0_list_input_op, true_style_label1_list_input_op = \
            _get_tensor_slice()

        reading_num_parallel_calls = self.thread_num - 1

        true_style_dataset = true_style_dataset.map(map_func=_parser_func,num_parallel_calls=reading_num_parallel_calls).batch(batch_size=self.config.trainParams.batchSize, drop_remainder=True).repeat(-1)
        true_style_iterator = true_style_dataset.make_initializable_iterator()
        true_style_img_tensor, true_style_label0_tensor_dense, true_style_label1_tensor_dense = \
            true_style_iterator.get_next()
        true_style_img_tensor = tf.cast(true_style_img_tensor,tf.float32)
        true_style_img_tensor, true_style_threshold = _random_thickness(input_tensor=true_style_img_tensor, fixed_mask=True)


        self.true_style_iterator = true_style_iterator
        self.true_style_data_list_input_op = true_style_data_list_input_op
        self.true_style_label0_list_input_op = true_style_label0_list_input_op
        self.true_style_label1_list_input_op = true_style_label1_list_input_op


        # for prototype images
        prototype_iterator_list = list()
        prototype_data_list_input_op_list = list()
        prototype_label0_list_input_op_list = list()
        prototype_label1_list_input_op_list = list()
        content_prototype_threshold = list()
        for ii in range(self.content_input_num):
            prototype_dataset, \
            prototype_data_list_input_op, \
            prototype_label0_list_input_op, prototype_label1_list_input_op = \
                _get_tensor_slice()
            prototype_dataset = \
                prototype_dataset.map(map_func=_parser_func,num_parallel_calls=reading_num_parallel_calls).batch(self.config.trainParams.batchSize, drop_remainder=True).repeat(-1)

            prototype_iterator = prototype_dataset.make_initializable_iterator()
            prototype_img_tensor, prototype_label0_tensor, prototype_label1_tensor = prototype_iterator.get_next()

            # data augment for content prototype w.r.t. random thickness
            prototype_img_tensor = tf.cast(prototype_img_tensor, tf.float32)
            prototype_img_tensor, current_threshold = \
                _random_thickness(input_tensor=prototype_img_tensor,
                                  fixed_mask=(augmentation.content.randThick))
            content_prototype_threshold.append(current_threshold)



            prototype_iterator_list.append(prototype_iterator)
            prototype_data_list_input_op_list.append(prototype_data_list_input_op)
            prototype_label0_list_input_op_list.append(prototype_label0_list_input_op)
            prototype_label1_list_input_op_list.append(prototype_label1_list_input_op)

            if ii == 0:
                all_prototype_tensor = prototype_img_tensor
            else:
                all_prototype_tensor = tf.concat([all_prototype_tensor,prototype_img_tensor], axis=3)
        all_prototype_tensor = tf.cast(all_prototype_tensor, tf.float32)


        if not self.content_input_number_actual == 0:
            for ii in range(self.config.trainParams.batchSize):
                current_prototype = tf.expand_dims(all_prototype_tensor[ii,:,:,:],axis=0)
                selected_indices = tf.random_uniform(shape=[self.content_input_number_actual, 1], minval=0,maxval=self.content_input_num,dtype=tf.int64)
                current_prototype_swapped = tf.transpose(current_prototype,[3,0,1,2])
                current_selected_prototype_swapped = tf.expand_dims(tf.squeeze(tf.nn.embedding_lookup(current_prototype_swapped,selected_indices)),axis=1)
                current_selected_prototype = tf.transpose(current_selected_prototype_swapped, [1, 2, 3, 0])
                if ii == 0:
                    all_prototype_tensor_new = current_selected_prototype
                else:
                    all_prototype_tensor_new = tf.concat([all_prototype_tensor_new,current_selected_prototype],axis=0)
            all_prototype_tensor = all_prototype_tensor_new
        else:
            self.content_input_number_actual = self.content_input_num


        self.prototype_iterator_list = prototype_iterator_list
        self.prototype_data_list_input_op_list = prototype_data_list_input_op_list
        self.prototype_label0_list_input_op_list = prototype_label0_list_input_op_list
        self.prototype_label1_list_input_op_list = prototype_label1_list_input_op_list


        # for reference images
        reference_iterator_list = list()
        reference_data_list_input_op_list = list()
        reference_label0_list_input_op_list = list()
        reference_label1_list_input_op_list = list()
        style_reference_threshold = list()
        for ii in range(self.config.datasetConfig.displayStyleNum):
            reference_dataset, \
            reference_data_list_input_op, \
            reference_label0_list_input_op, reference_label1_list_input_op = \
                _get_tensor_slice()

            reference_dataset = reference_dataset.map(map_func=_parser_func,num_parallel_calls=reading_num_parallel_calls).batch(self.config.trainParams.batchSize,drop_remainder=True).repeat(-1)
            reference_iterator = reference_dataset.make_initializable_iterator()
            reference_img_tensor, reference_label0_tensor, reference_label1_tensor = reference_iterator.get_next()

            # data augment for reference style w.r.t. random thickness
            reference_img_tensor = tf.cast(reference_img_tensor, tf.float32)
            reference_img_tensor, current_threshold = \
                _random_thickness(input_tensor=reference_img_tensor,
                                  fixed_mask=(augmentation.content.randThick))
            style_reference_threshold.append(current_threshold)

            reference_iterator_list.append(reference_iterator)
            reference_data_list_input_op_list.append(reference_data_list_input_op)
            reference_label0_list_input_op_list.append(reference_label0_list_input_op)
            reference_label1_list_input_op_list.append(reference_label1_list_input_op)

            if ii == 0:
                all_reference_tensor = reference_img_tensor
            else:
                all_reference_tensor = tf.concat([all_reference_tensor, reference_img_tensor], axis=3)
        all_reference_tensor = tf.cast(all_reference_tensor, tf.float32)


        self.reference_iterator_list=reference_iterator_list
        self.reference_data_list_input_op_list = reference_data_list_input_op_list
        self.reference_label0_list_input_op_list = reference_label0_list_input_op_list
        self.reference_label1_list_input_op_list = reference_label1_list_input_op_list

        true_style_label0_tensor_onehot =_convert_label_to_one_hot(dense_label=true_style_label0_tensor_dense,
                                                                   voc=self.label0_vec)
        true_style_label1_tensor_onehot =_convert_label_to_one_hot(dense_label=true_style_label1_tensor_dense,
                                                                   voc=discrminator_label1_vec)
        



        # data augmentation
        if not augmentation.different:
            img_all = tf.concat([true_style_img_tensor, all_prototype_tensor, all_reference_tensor], axis=3)
            
            for ii in range(self.config.trainParams.batchSize):
                thisImg = img_all[ii, :, :, :]
                if augmentation.content.translation:
                    translated = self.ImageTranslateAugmentation(inputImg=thisImg)
                else:
                    translated = thisImg
                    
                if augmentation.content.rotation:
                    rotated = self.ImageRotationAugmentation(inputImg=translated)
                else:
                    rotated = translated
                
                if augmentation.content.flip:
                    flipped = self.ImageFlipAugmentation(inputImg=rotated)
                else:
                    flipped = rotated
                resulted = tf.expand_dims(flipped, axis=0)
                if ii == 0:
                    img_all_new = resulted
                else:
                    img_all_new = tf.concat([img_all_new, resulted],axis=0)
            img_all = img_all_new

            true_style_img_tensor = tf.expand_dims(img_all[:,:,:,0],axis=3)
            all_prototype_tensor = img_all[:,:,:,1:int(all_prototype_tensor.shape[3])+1]
        else:
            # augment for content and true style
            imgTogether = tf.concat([true_style_img_tensor, all_prototype_tensor], axis=3)
            for ii in range(self.config.trainParams.batchSize):
                thisImg = imgTogether[ii, :, :, :]
                if augmentation.content.translation:
                    translated = self.ImageTranslateAugmentation(inputImg=thisImg)
                else:
                    translated = thisImg
                if augmentation.content.rotation:
                    rotated = self.ImageRotationAugmentation(inputImg=translated)
                else:
                    rotated = translated
                
                if augmentation.content.flip:
                    flipped = self.ImageFlipAugmentation(inputImg=rotated)
                else:
                    flipped = rotated
                resulted = tf.expand_dims(flipped, axis=0)
                if ii == 0:
                    imgTogetherNew = resulted
                else:
                    imgTogetherNew = tf.concat([imgTogetherNew, resulted],axis=0)
            imgTogether=imgTogetherNew
            true_style_img_tensor=tf.expand_dims(imgTogether[:,:,:,0], axis=3)
            all_prototype_tensor=imgTogether[:,:,:,1:]
                    
            # augment for style references
            # styleTogether = tf.concat([all_reference_tensor], axis=3)
            styleTogether = tf.concat([all_reference_tensor], axis=3)
            for ii in range(self.config.trainParams.batchSize):
                for jj in range(int(styleTogether.shape[3])):
                    thisStyle = tf.expand_dims(styleTogether[ii,:,:,jj], axis=2)
                    if augmentation.content.translation:
                        translated = self.ImageTranslateAugmentation(inputImg=thisStyle, cropPctg=0.5)
                    else:
                        translated = thisImg
                    if augmentation.content.rotation:
                        rotated = self.ImageRotationAugmentation(inputImg=translated)
                    else:
                        rotated = translated
                    
                    if augmentation.content.flip:
                        flipped = self.ImageFlipAugmentation(inputImg=rotated)
                    else:
                        flipped = rotated
                    resulted = tf.expand_dims(flipped, axis=0)
                    if jj==0:
                        thisBatchImgs = resulted
                    else:
                        thisBatchImgs = tf.concat([thisBatchImgs, resulted], axis=3)
                if ii == 0:
                    newStyles = thisBatchImgs
                else:
                    newStyles = tf.concat([newStyles, thisBatchImgs],axis=0)
            styleTogether=newStyles
            all_reference_tensor = styleTogether[:,:,:,:self.config.datasetConfig.displayStyleNum]


        true_style_img_tensor = (true_style_img_tensor - 0.5) * 2
        all_prototype_tensor = (all_prototype_tensor - 0.5) * 2
        all_reference_tensor = (all_reference_tensor - 0.5) * 2

        self.output_tensor_list = list()
        self.output_tensor_list.append(true_style_img_tensor) # 0
        self.output_tensor_list.append(all_prototype_tensor)  # 1
        self.output_tensor_list.append(all_reference_tensor)  # 2
        self.output_tensor_list.append(true_style_label0_tensor_onehot)  # 3
        self.output_tensor_list.append(true_style_label1_tensor_onehot)  # 4
        self.output_tensor_list.append(true_style_label0_tensor_dense)   # 5
        self.output_tensor_list.append(true_style_label1_tensor_dense)   # 6
        self.output_tensor_list.append(true_style_threshold) # 7
        self.output_tensor_list.append(content_prototype_threshold) # 8
        self.output_tensor_list.append(style_reference_threshold) # 9


    def get_next_batch(self, sess):
        true_style,prototype,reference, \
        onehot_label0, onehot_label1, \
        dense_label0, dense_label1, \
        true_style_threshold, content_threshold, style_threshold = \
            sess.run([self.output_tensor_list[0],
                      self.output_tensor_list[1],
                      self.output_tensor_list[2],
                      self.output_tensor_list[3],
                      self.output_tensor_list[4],
                      self.output_tensor_list[5],
                      self.output_tensor_list[6],
                      self.output_tensor_list[7],
                      self.output_tensor_list[8],
                      self.output_tensor_list[9],
                      ])
        return true_style,prototype,reference, \
               onehot_label0, onehot_label1, \
               dense_label0, dense_label1, \
               true_style_threshold, content_threshold, style_threshold
               
               
    def ImageTranslateAugmentation(self, inputImg, cropPctg=0.25):
        current_img = inputImg
        crop_size = tf.random_uniform(shape=[],
                                        minval=int(int(inputImg.shape[1])*(1-cropPctg)),
                                        maxval=int(inputImg.shape[1])+1, dtype=tf.int32)
        cropped_img = tf.random_crop(value=current_img,
                                        size=[crop_size, crop_size, int(inputImg.shape[2])])
        cropped_img = tf.image.resize_images(cropped_img, [self.config.datasetConfig.imgWidth, self.config.datasetConfig.imgWidth])
        cropped_img = tf.reshape(cropped_img, [int(inputImg.shape[0]), int(inputImg.shape[1]),int(inputImg.shape[2])])
        return cropped_img

    
    def ImageFlipAugmentation(self, inputImg):
        orgImage = inputImg
        flip_img = tf.image.random_flip_up_down(tf.image.random_flip_left_right(inputImg))
        threshold = tf.random_uniform(shape=[], minval=0, maxval=1,dtype=tf.float32)
        nonFlip = lambda : orgImage
        flip = lambda: flip_img
        flip_img = tf.case([(tf.less(threshold, 0.5), nonFlip)], default=flip)
        return flip_img
    
    def ImageRotationAugmentation(self, inputImg):
        orgImage = inputImg
        rotateImg = lambda: tf.transpose(orgImage,[1,0,2])
        non_rotate_flip = lambda : orgImage
        threshold = tf.random_uniform(shape=[], minval=0, maxval=1,dtype=tf.float32)
        resultImg = tf.case([(tf.less(threshold, 0.5), rotateImg)], default=non_rotate_flip)
        return resultImg

            
            
class DataProvider(object):
    def __init__(self,
                 config,
                 content_input_number_actual=ContentInputNumberActual,
                 max_style_reference_loss_num=MaxStyleReferenceLossNum,
                 fixed_style_reference_dir=None,
                 fixed_file_list_txt_style_reference=None,
                 dataset_mode='Train',
                 fixed_char_list_txt=None):

        
        
        local_device_protos = device_lib.list_local_devices()
        gpu_device = [x.name for x in local_device_protos if x.device_type == 'GPU']
        if len(gpu_device) == 0:
            self.thread_num = multi_thread.cpu_count()
        else:
            self.thread_num = int(multi_thread.cpu_count() / len(gpu_device))

        self.config=config
        self.content_input_number_actual=content_input_number_actual
        self.max_style_reference_loss_num=max_style_reference_loss_num
        self.config.datasetConfig.displayStyleNum = max(self.config.datasetConfig.inputStyleNum, displayStyleNum)
        self.dataset_iterator_create(dataset_mode=dataset_mode)
        
        if dataset_mode=='Eval':
            fixed_style_reference_label1_list, fixed_style_reference_label0_list, fixed_style_reference_data_list = \
                self.data_file_list_read(file_list_txt=fixed_file_list_txt_style_reference,
                                         file_data_dir=fixed_style_reference_dir)

            fixed_style_reference_data_list, \
            fixed_style_reference_label0_list, \
            fixed_style_reference_label1_list,\
                = self.eliminate_invalid_repeated_data(data_list=fixed_style_reference_data_list,
                                                       label0_list=fixed_style_reference_label0_list,
                                                       label1_list=fixed_style_reference_label1_list)

            fixed_style_reference_list,fixed_style_reference_data_path_list, char_list = \
                self.data_sort_by_fixed_label0_order(label1_list=fixed_style_reference_label1_list,
                                                     label0_list=fixed_style_reference_label0_list,
                                                     data_list=fixed_style_reference_data_list,
                                                     fixed_char_list_txt=fixed_char_list_txt)
            self.train_iterator.fixed_style_reference_image_list = fixed_style_reference_list
            self.train_iterator.fixed_style_reference_data_path_list = fixed_style_reference_data_path_list
            self.train_iterator.fixed_style_reference_char_list = char_list
            print(print_separator)





    def dataset_reinitialization(self, sess, init_for_val, info_interval):
        self.train_iterator.reproduce_dataset_lists(info="TrainData", shuffle=True, info_print_interval=info_interval)
        self.train_iterator.iterator_reset(sess=sess)
        if init_for_val:
            self.validate_iterator.reproduce_dataset_lists(info="ValData", shuffle=False, info_print_interval=info_interval)
            self.validate_iterator.iterator_reset(sess=sess)
        print(print_separator)

    def eliminate_invalid_repeated_data(self,data_list, label0_list, label1_list):

        output_data_list = list()
        output_label0_list = list()
        output_label1_list = list()
        tmp_counter = 0
        for label1 in np.unique(label1_list).tolist():
            related_indices = [ii for ii in range(len(label1_list)) if label1_list[ii]==label1]
            for jj in related_indices:
                current_data = data_list[jj]
                if not 'TmpChars' in current_data:
                    output_data_list.append(data_list[jj])
                    output_label0_list.append(label0_list[jj])
                    output_label1_list.append(label1_list[jj])
                    tmp_counter+=1
                else:
                    print("Delete:%s" % current_data)
                if tmp_counter==0:
                    print("ERROR: No Real Style for %s" % label1)
                    return -1,-1,-1
        return data_list, label0_list, label1_list


    def data_file_list_read(self,datasetConfig):

        label0_list = list()
        label1_list = list()
        data_list = list()

        for ii in range(len(datasetConfig.txtPath)):

            file_handle = open(datasetConfig.txtPath[ii], 'r')
            lines = file_handle.readlines()

            for line in lines:
                curt_line = line.split('@')
                this_label0 = curt_line[1]
                this_label1=curt_line[2]

                if len(this_label1)<LABEL_LENGTH and not this_label1 == '-1':
                    for jj in range(LABEL_LENGTH-len(this_label1)):
                        this_label1 = '0'+ this_label1

                label1_list.append(this_label1)
                label0_list.append(curt_line[1])




                curt_data = curt_line[3].split('\n')[0]
                if curt_data[0] == '/':
                    curt_data = curt_data[1:]
                curt_data_path = os.path.join(datasetConfig.dataPath[ii], curt_data)
                data_list.append(curt_data_path)
                # print(curt_data)
            file_handle.close()
        return label1_list, label0_list, data_list

    def data_sort_by_fixed_label0_order(self,fixed_char_list_txt,label1_list,label0_list,data_list):

        def read_content_from_dir():
            # get label0 for the targeted content input txt
            chars_list = list()
            with open(fixed_char_list_txt) as f:
                for line in f:

                    line = u"%s" % line
                    char_counter = 0
                    for char in line:

                        current_char = line[char_counter]
                        char_counter += 1
                        chars_list.append(current_char)


            return chars_list

        char_list = read_content_from_dir()
        label0_vec = list()
        label1_vec = np.unique(label1_list)
        print(print_separator)
        print("Fixed Label1 Order:")
        print(label1_vec)
        print(print_separator)
        for label0 in label0_list:
            if not label0 in label0_vec:
                label0_vec.append(label0)
        label0_counter=0
        output_img_list=list()
        output_data_path_list=list()
        print("Fixed Char Lists:")
        for label0 in label0_vec:
            label0_counter+=1
            print_str="%s|" % (label0)
            relevant_indices_label0 = [ii for ii in range(len(label0_list)) if label0_list[ii]==label0]
            current_label1_list=list()
            current_label1_data_list=list()
            current_label1_label0_list=list()
            for ii in relevant_indices_label0:
                current_label1_list.append(label1_list[ii])
                current_label1_data_list.append(data_list[ii])
                current_label1_label0_list.append(label0_list[ii])

            current_label1_img_matrix_list=list()
            current_data_path_list=list()
            for label1 in label1_vec:
                relevant_indices_label1 = [jj for jj in range(len(current_label1_list)) if current_label1_list[jj]==label1]
                current_label0_current_label1_img_matrix = np.zeros(shape=[len(relevant_indices_label1),self.input_width,self.input_width,1])
                current_current_data_path_list=list()
                counter=0
                for jj in relevant_indices_label1:
                    char_read=misc.imread(current_label1_data_list[jj])
                    char_read = char_read/GRAYSCALE_AVG-1
                    if np.ndim(char_read)==3:
                        char_read=char_read[:,:,0]
                    char_read=np.expand_dims(char_read,axis=2)
                    current_label0_current_label1_img_matrix[counter,:,:,:]=char_read
                    current_current_data_path_list.append(current_label1_data_list[jj])
                    counter+=1
                    # image_show(tmp)
                    # print("%s||%s||%s" % (current_label1_data_list[jj].split("/")[-1],
                    #                       current_label1_list[jj],
                    #                       current_label1_label0_list[jj]))
                print_str = print_str + "%2d|" % len(relevant_indices_label1)
                current_label1_img_matrix_list.append(current_label0_current_label1_img_matrix)
                current_data_path_list.append(current_current_data_path_list)
            print(print_str)
            # image_show(char_read)
            output_img_list.append(current_label1_img_matrix_list)
            output_data_path_list.append(current_data_path_list)
        return output_img_list, output_data_path_list, char_list,

    def dataset_iterator_create(self,dataset_mode='Train'):

        def _filter_current_label1_data(current_label1, full_data_list, full_label1_list,full_label0_list):
            selected_indices = [ii for ii in range(len(full_label1_list)) if full_label1_list[ii] == current_label1]
            selected_data_list=list()
            selected_label0_list = list()
            selected_label1_list = list()

            for ii in selected_indices:
                selected_data_list.append(full_data_list[ii])
                selected_label0_list.append(full_label0_list[ii])
                selected_label1_list.append(full_label1_list[ii])
            return selected_data_list, selected_label0_list,selected_label1_list

        # building for content data set
        content_label1_list, content_label0_list, content_data_path_list = \
            self.data_file_list_read(datasetConfig=self.config.datasetConfig.contentData)
        self.content_label1_vec = np.unique(content_label1_list)
        self.content_label0_vec = np.unique(content_label0_list)
        self.content_input_num = len(np.unique(content_label1_list))



        content_prototype_list = list()
        for content_label1 in self.content_label1_vec:
            current_data_list, current_label0_list, current_label1_list = \
                _filter_current_label1_data(current_label1=content_label1,
                                            full_data_list=content_data_path_list,
                                            full_label0_list=content_label0_list,
                                            full_label1_list=content_label1_list)
            train_content_dataset = Dataset(data_list=cpy.deepcopy(current_data_list),
                                            label0_list=cpy.deepcopy(current_label0_list),
                                            label1_list=cpy.deepcopy(current_label1_list),
                                            sorted_by_label0=False,
                                            # print_marks='ForOriginalContentData:',
                                            info_print_interval=printInfoSec)
            content_prototype_list.append(train_content_dataset)

        # building the validate data
        validation_style_label1_list, validation_style_label0_list, validation_style_data_path_list = \
            self.data_file_list_read(datasetConfig=self.config.datasetConfig.styleDataValidate)

        validation_style_reference_list = list()
        for ii in range(self.config.datasetConfig.displayStyleNum):
            validation_style_dataset = Dataset(data_list=cpy.deepcopy(validation_style_data_path_list),
                                                label0_list=cpy.deepcopy(validation_style_label0_list),
                                                label1_list=cpy.deepcopy(validation_style_label1_list),
                                                sorted_by_label0=False,
                                                info_print_interval=printInfoSec)
            validation_style_reference_list.append(validation_style_dataset)



        # building for true style data set for validation
        validation_true_style_dataset = Dataset(data_list=cpy.deepcopy(validation_style_data_path_list),
                                                label0_list=cpy.deepcopy(validation_style_label0_list),
                                                label1_list=cpy.deepcopy(validation_style_label1_list),
                                                sorted_by_label0=True,
                                                info_print_interval=printInfoSec)

        # construct the validation iterator
        self.validate_iterator = Dataset_Iterator(config=self.config,
                                                  thread_num=self.thread_num,
                                                  true_style=validation_true_style_dataset,
                                                  style_reference_list=cpy.deepcopy(validation_style_reference_list),
                                                  content_prototype_list=cpy.deepcopy(content_prototype_list),
                                                  content_input_number_actual=self.content_input_number_actual)
        

        

        self.validate_iterator.create_dataset_op(discrminator_label1_vec=self.validate_iterator.label1_vec, augmentation=self.config.datasetConfig.augmentation.test)
        
        

        # building for style data set for train
        train_style_label1_list, train_style_label0_list, train_style_data_path_list = \
            self.data_file_list_read(datasetConfig=self.config.datasetConfig.styleDataTrain)

        train_style_reference_list = list()
        for ii in range(self.config.datasetConfig.displayStyleNum):
            train_style_dataset = Dataset(data_list=cpy.deepcopy(train_style_data_path_list),
                                          label0_list=cpy.deepcopy(train_style_label0_list),
                                          label1_list=cpy.deepcopy(train_style_label1_list),
                                          sorted_by_label0=False,
                                        #   print_marks='ForStyleReferenceTrainData:',
                                          info_print_interval=printInfoSec)
            train_style_reference_list.append(train_style_dataset)


        # building for true style data set for train
        train_true_style_dataset = Dataset(data_list=cpy.deepcopy(train_style_data_path_list),
                                           label0_list=cpy.deepcopy(train_style_label0_list),
                                           label1_list=cpy.deepcopy(train_style_label1_list),
                                           sorted_by_label0=False,
                                           info_print_interval=printInfoSec)

        # construct the train iterator
        self.train_iterator = Dataset_Iterator(config=self.config,
                                               thread_num=self.thread_num,
                                               true_style=train_true_style_dataset,
                                               style_reference_list=cpy.deepcopy(train_style_reference_list),
                                               content_prototype_list=cpy.deepcopy(content_prototype_list),
                                               content_input_number_actual=self.content_input_number_actual)
        self.style_label0_vec = np.unique(self.train_iterator.label0_vec).tolist()
        self.style_label1_vec = np.unique(self.train_iterator.label1_vec).tolist()
        self.train_iterator.create_dataset_op(discrminator_label1_vec=self.train_iterator.label1_vec, augmentation=self.config.datasetConfig.augmentation.train)

        
        
        

        print(print_separator)
        self.full_label0_vec = list()
        self.full_label1_vec = list()
        self.full_label0_vec.extend(train_style_label0_list)
        self.full_label0_vec.extend(validation_style_label0_list)
        self.full_label1_vec.extend(train_style_label1_list)
        self.full_label1_vec.extend(validation_style_label1_list)
        self.full_label0_vec=np.unique(self.full_label0_vec)

        unique_label1_vec = np.unique(self.full_label1_vec)
        fixed_label_vec = list()
        for ii in unique_label1_vec:
            this_fix_label = ii
            if len(ii)<LABEL_LENGTH:
                for jj in range(LABEL_LENGTH-len(ii)):
                    this_fix_label = '0'+ this_fix_label
            fixed_label_vec.append(this_fix_label)
        self.full_label1_vec=fixed_label_vec
        self.full_label1_vec.sort()

    def get_involved_label_list(self):
        return self.style_label0_vec,self.style_label1_vec

    def compute_total_train_batch_num(self):
        """Total padded batch num"""
        return int(np.ceil(len(self.train_iterator.true_style.data_list) / float(self.config.trainParams.batchSize)))
        
    
    def compute_total_validate_batch_num(self):
        """Total padded batch num"""
        return int(np.ceil(len(self.validate_iterator.true_style.data_list) / float(self.config.trainParams.batchSize)))
