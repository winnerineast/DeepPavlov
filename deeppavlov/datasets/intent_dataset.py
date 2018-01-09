from pathlib import Path
import copy

import numpy as np
from sklearn.model_selection import train_test_split

from deeppavlov.core.common.registry import register
from deeppavlov.core.data.dataset import Dataset
from deeppavlov.core.common import paths
from deeppavlov.models.preprocessors.preprocessors import PREPROCESSORS


@register('intent_dataset')
class IntentDataset(Dataset):
    def __init__(self, data, dataset_path=None, dataset_dir='intents', dataset_file='classes.txt',
                 seed=None, extract_classes=True, classes_file=None,
                 fields_to_merge=None, merged_field=None,
                 field_to_split=None, split_fields=None, split_proportions=None,
                 prep_method_name: str = None,
                 *args, **kwargs):

        super().__init__(data, seed)
        self.classes = None

        if extract_classes:
            self.classes = self._extract_classes()
            if classes_file is None:
                if dataset_path is None:
                    ser_dir = Path(paths.USR_PATH).joinpath(dataset_dir)
                    if not ser_dir.exists():
                        ser_dir.mkdir()
                    classes_file = Path(paths.USR_PATH).joinpath(dataset_dir, dataset_file)
                else:
                    ser_dir = Path(dataset_path).joinpath(dataset_dir)
                    if not ser_dir.exists():
                        ser_dir.mkdir()
                    classes_file = ser_dir.joinpath(dataset_file)

            print("No file name for classes provided. Classes are saved to file {}".format(
                classes_file))
            with open(Path(classes_file), 'w') as fin:
                for i in range(len(self.classes)):
                    fin.write(self.classes[i] + '\n')
        if fields_to_merge is not None:
            if merged_field is not None:
                print("Merging fields <<{}>> to new field <<{}>>".format(fields_to_merge,
                                                                         merged_field))
                self._merge_data(fields_to_merge=fields_to_merge.split(' '),
                                 merged_field=merged_field)
            else:
                raise IOError("Given fields to merge BUT not given name of merged field")

        if field_to_split is not None:
            if split_fields is not None:
                print("Splitting field <<{}>> to new fields <<{}>>".format(field_to_split,
                                                                           split_fields))
                self._split_data(field_to_split=field_to_split,
                                 split_fields=split_fields.split(" "),
                                 split_proportions=[float(s) for s in
                                                    split_proportions.split(" ")])
            else:
                raise IOError("Given field to split BUT not given names of split fields")

        self.prep_method_name = prep_method_name

        if prep_method_name:
            self.data = self.preprocess(PREPROCESSORS[prep_method_name])

    def _extract_classes(self):
        intents = []
        all_data = self.iter_all(data_type='train')
        for sample in all_data:
            intents.extend(sample[1])
        if 'valid' in self.data.keys():
            all_data = self.iter_all(data_type='valid')
            for sample in all_data:
                intents.extend(sample[1])
        intents = np.unique(intents)
        return np.array(sorted(intents))

    def _split_data(self, field_to_split, split_fields, split_proportions):
        data_to_div = self.data[field_to_split].copy()
        data_size = len(self.data[field_to_split])
        for i in range(len(split_fields) - 1):
            self.data[split_fields[i]], \
            data_to_div = train_test_split(data_to_div,
                                           test_size=
                                           len(data_to_div) - int(
                                               data_size * split_proportions[i]))
        self.data[split_fields[-1]] = data_to_div
        return True

    def _merge_data(self, fields_to_merge, merged_field):
        data = self.data.copy()
        data[merged_field] = []
        for name in fields_to_merge:
            data[merged_field] += self.data[name]
        self.data = data
        return True

    def preprocess(self, prep_method):

        data_copy = copy.deepcopy(self.data)

        for data_type in self.data:
            chunk = self.data[data_type]
            for i, sample in enumerate(chunk):
                data_copy[i] = (prep_method([sample[0]])[0], chunk[i][1])
        return data_copy