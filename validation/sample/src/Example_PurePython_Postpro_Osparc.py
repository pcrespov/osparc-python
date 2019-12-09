#!/usr/bin/env python
# coding: utf-8

import os
import numpy as np
import pickle

import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns
import imgkit

RAW_DATA = r'./data/results.pkl'
OUTPUTS_DIR = r'./outputs'
assert os.path.exists(RAW_DATA)
if not os.path.exists(OUTPUTS_DIR):
    os.makedirs(OUTPUTS_DIR)

results = pickle.load(open(RAW_DATA, 'rb'), encoding='latin1')


def highlight_max(data, color='yellow'):
    '''
    highlight the maximum in a Series or DataFrame
    # https://stackoverflow.com/questions/45606458/python-pandas-highlighting-maximum-value-in-column
    '''
    attr = 'font-weight: bold'  # 'background-color: {}'.format(color)
    if data.ndim == 1:  # Series from .apply(axis=0) or axis=1
        is_max = data == data.max()
        return [attr if v else '' for v in is_max]
    else:  # from .apply(axis=None)
        is_max = data == data.max().max()
        return pd.DataFrame(np.where(is_max, attr, ''), index=data.index, columns=data.columns)


def to_multiindex(data_table):
    def _split_column_name(name):
        tokens = name.split('|')
        return [t for t in tokens]

    tokens = [_split_column_name(a) for a in data_table.columns]
    max_level = max([len(token) for token in tokens])
    for token in tokens:
        if len(token) < max_level:
            token.extend([np.nan for _ in range(max_level - len(token))])
    res = data_table.copy()

    tuples = [tuple('' if pd.isnull(x[i]) else x[i] for i in range(max_level)) for x in tokens]
    res.columns = pd.MultiIndex.from_tuples(tuples)
    return res


_ALL_FIGURES = []


def save_table(styled_table, figname, show=False, quality=89, latex_order=9999, latex_caption=''):
    html_table = styled_table.render()
    options = {'quiet': '', 'quality': quality}
    figpath = os.path.join(OUTPUTS_DIR, figname)
    if not os.path.exists(os.path.dirname(figpath)):
        os.makedirs(os.path.dirname(figpath))
    imgkit.from_string(html_table, figpath, options=options)
    print('Created table: {}'.format(figpath))
    if latex_order is not None:
        _ALL_FIGURES.append({'path': figpath, 'order': latex_order, 'caption': latex_caption})


def save_figure(fig, figname, dpi=100, latex_order=9999, latex_caption=''):
    figpath = os.path.join(OUTPUTS_DIR, figname)
    if not os.path.exists(os.path.dirname(figpath)):
        os.makedirs(os.path.dirname(figpath))
    fig.savefig(figpath, bbox_inches='tight', dpi=dpi)
    print('Created figure: {}'.format(figpath))
    if latex_order is not None:
        _ALL_FIGURES.append({'path': figpath, 'order': latex_order, 'caption': latex_caption})
    plt.close(fig)


df = pd.DataFrame(results)
df['model'] = df['model'] + '_' + df['version']
for col in ['freq', 'bc', 'model', 'pol']:
    df[col] = df[col].astype('category')

for col in ['pbMass', 'wbMass', 'hMass']:
    df[col] = df[col].astype('float64')
df.head()

df = df[(df.pol == 'CP')]

pd.options.display.float_format = '{:,.2f}'.format

# Apply normalization factors

# rescale E fields to 1muT (rms) incident B1 field at isocentre of empty RF coil
df['ErmsHead_1mu'] = df['ErmsHead_raw'] / df['B1rms_empty']
df['ErmsLimbs_1mu'] = df['ErmsLimbs_raw'] / df['B1rms_empty']
df['ErmsBody_1mu'] = df['ErmsBody_raw'] / df['B1rms_empty']

# rescale SAR values to 1muT (rms) incident B1 field at isocentre of empty RF coil
df['hSAR_1mu'] = df['hSAR_raw'] / (df['B1rms_empty']**2)
df['wbSAR_1mu'] = df['wbSAR_raw'] / (df['B1rms_empty']**2)
df['pbSAR_1mu'] = df['pbSAR_raw'] / (df['B1rms_empty']**2)

df['pbSARlimitNormal'] = 10.0 - 8.0 * df['pbMass'] / df['wbMass']
df['pbSARlimitFirst'] = 10.0 - 6.0 * df['pbMass'] / df['wbMass']

c1 = 3.2 / df['hSAR_1mu']
c2n = 2.0 / df['wbSAR_1mu']
c2f = 4.0 / df['wbSAR_1mu']
c3n = df['pbSARlimitNormal'] / df['pbSAR_1mu']
c3f = df['pbSARlimitFirst'] / df['pbSAR_1mu']

df['limitNormal'] = '-'
df.loc[c1 <= np.minimum(c2n, c3n), 'limitNormal'] = 'h'
df.loc[c2n <= np.minimum(c1, c3n), 'limitNormal'] = 'wb'
df.loc[c3n <= np.minimum(c1, c2n), 'limitNormal'] = 'pb'
df['limitFirst'] = '-'
df.loc[c1 <= np.minimum(c2f, c3f), 'limitFirst'] = 'h'
df.loc[c2f <= np.minimum(c1, c3f), 'limitFirst'] = 'wb'
df.loc[c3f <= np.minimum(c1, c2f), 'limitFirst'] = 'pb'

# scaling factors at operating modes
df['ScalingNormal'] = np.minimum(
    7.0,
    np.sqrt(
        np.minimum(np.minimum(3.2 / df['hSAR_1mu'], 2.0 / df['wbSAR_1mu']), df['pbSARlimitNormal'] / df['pbSAR_1mu'])))
df['ScalingFirst'] = np.minimum(
    7.0,
    np.sqrt(np.minimum(np.minimum(3.2 / df['hSAR_1mu'], 4.0 / df['wbSAR_1mu']),
                       df['pbSARlimitFirst'] / df['pbSAR_1mu'])))

# rescale E fields to SAR limits at operating modes
df['ErmsHeadNormalOM'] = df['ErmsHead_1mu'] * df['ScalingNormal']
df['ErmsLimbsNormalOM'] = df['ErmsLimbs_1mu'] * df['ScalingNormal']
df['ErmsBodyNormalOM'] = df['ErmsBody_1mu'] * df['ScalingNormal']

df['ErmsHeadFirstOM'] = df['ErmsHead_1mu'] * df['ScalingFirst']
df['ErmsLimbsFirstOM'] = df['ErmsLimbs_1mu'] * df['ScalingFirst']
df['ErmsBodyFirstOM'] = df['ErmsBody_1mu'] * df['ScalingFirst']

df['B1plusRatioI'] = df['B1rmsIiso'] / df['B1rms']
df['B1plusRatioQ'] = df['B1rmsQiso'] / df['B1rms']

# check that none of the SAR limits are exceeded
_eps = 1e-14  # machine precision tolerance
assert all(df['pbSAR_1mu'] * (df['ScalingNormal']**2) <= df['pbSARlimitNormal'] + _eps)
assert all(df['pbSAR_1mu'] * (df['ScalingFirst']**2) <= df['pbSARlimitFirst'] + _eps)
assert all(df['hSAR_1mu'] * (df['ScalingNormal']**2) <= 3.2 + _eps)
assert all(df['wbSAR_1mu'] * (df['ScalingNormal']**2) <= 2.0 + _eps)
assert all(df['hSAR_1mu'] * (df['ScalingFirst']**2) <= 3.2 + _eps)
assert all(df['wbSAR_1mu'] * (df['ScalingFirst']**2) <= 4.0 + _eps)

df.head()
df.describe()

renaming_dict = {
    'ErmsFirstOM_max': 'Erms First-Level Operating Mode (V/m)',
    'ErmsFirstOM': 'Erms First-Level Operating Mode (V/m)',
    'ErmsFirst': 'Erms First-Level Operating Mode (V/m)',
    'ErmsNormalOM_max': 'Erms Normal Operating Mode (V/m)',
    'ErmsNormalOM': 'Erms Normal Operating Mode (V/m)',
    'ErmsNormal': 'Erms Normal Operating Mode (V/m)',
    'Erms_1mu_max': 'Erms per 1 muT incident B1 field (V/m)',
    'Erms': 'Erms per 1 muT incident B1 field (V/m)',
    'Body': 'Trunk',
    'Limbs': 'Limbs',
    'freq': 'Frequency',
    'pos': 'Position (mm)',
    'B1 RMS': 'B1 RMS (muT)',
    'limit': 'SAR limit'
}

df[(df.model == 'Fats_V3.2')]

# # Tables P1-P4 like in AnnexP (single birdcage)
# For both 1.5T and 3.0T

cm = sns.light_palette((1, 0.7, 0.6), as_cmap=True)  #, as_cmap=True)

models = ['Fats_V3.2', 'Fats_V3', 'Duke_V3', 'Louis_V3', 'Ella_V3']

for model, frequency in [(_m, _f) for _m in models for _f in [64, 128]]:
    birdcage = 'HP_B70_L60'
    dff = df[(df.model == model) & (df.freq == frequency) & (df.bc == birdcage) & (df.pos <= 1500) & (df.pol == 'CP')]
    cols = [
        'pos', 'ErmsHead_1mu', 'ErmsBody_1mu', 'ErmsLimbs_1mu', 'ScalingNormal', 'ScalingFirst', 'limitNormal',
        'ErmsHeadNormalOM', 'ErmsBodyNormalOM', 'ErmsLimbsNormalOM', 'limitFirst', 'ErmsHeadFirstOM', 'ErmsBodyFirstOM',
        'ErmsLimbsFirstOM'
    ]
    old_names = [
        'ErmsHead_1mu', 'ErmsBody_1mu', 'ErmsLimbs_1mu', 'ErmsHeadNormalOM', 'ErmsBodyNormalOM', 'ErmsLimbsNormalOM',
        'ErmsHeadFirstOM', 'ErmsBodyFirstOM', 'ErmsLimbsFirstOM', 'ScalingNormal', 'ScalingFirst', 'limitNormal',
        'limitFirst'
    ]
    new_names = [
        'Erms|Head', 'Erms|Body', 'Erms|Limbs', 'ErmsNormal|Head', 'ErmsNormal|Body', 'ErmsNormal|Limbs',
        'ErmsFirst|Head', 'ErmsFirst|Body', 'ErmsFirst|Limbs', 'Scaling Factor|Normal', 'Scaling Factor|First Level',
        'limit|Normal', 'limit|First Level'
    ]
    dff = dff[cols].rename(columns={o: n for o, n in zip(old_names, new_names)})
    dff = to_multiindex(dff)
    table = dff.rename(columns=renaming_dict).style.background_gradient(
        cmap=cm).apply(highlight_max).set_table_attributes(
            'border=1 cellspacing="3" cellpadding="10" style="text-align: center"').set_precision(3).set_caption(
                'Induced Erms - {} {}MHz'.format(model, frequency)).hide_index()  #.format("{0:.2g}")
    latex_caption = '[Same as AnnexP tables P1-P4] Model: {}, Frequency: {} MHz, Birdcage: {}'.format(
        model, frequency, birdcage)
    save_table(table,
               'single_birdcage/{freq}/table_{bc}_{m}_{freq}.png'.format(bc=birdcage, m=model, freq=frequency),
               show=True,
               latex_order=2,
               latex_caption=latex_caption)

    dff.rename(columns=renaming_dict).to_excel(r'D:\mrixvip\annexP\tableP1_{}_{}.xlsx'.format(model, frequency))

# ## Table P5 like in AnnexP (single birdcage)
# for both 1.5T and 3.0T

for frequency in [64, 128]:
    birdcage = 'HP_B70_L60'
    dff = df[(df.freq == frequency) & (df.bc == birdcage) & (df.pos <= 900) & (df.pol == 'CP')]

    def get_maxima(x):
        old_names = [
            'ErmsHead_1mu', 'ErmsBody_1mu', 'ErmsLimbs_1mu', 'ErmsHeadNormalOM', 'ErmsBodyNormalOM',
            'ErmsLimbsNormalOM', 'ErmsHeadFirstOM', 'ErmsBodyFirstOM', 'ErmsLimbsFirstOM'
        ]
        new_names = [
            'Erms|Head', 'Erms|Body', 'Erms|Limbs', 'ErmsNormal|Head', 'ErmsNormal|Body', 'ErmsNormal|Limbs',
            'ErmsFirst|Head', 'ErmsFirst|Body', 'ErmsFirst|Limbs'
        ]
        new_df = pd.DataFrame()
        for q1, q2 in zip(old_names, new_names):
            new_df[q2] = np.array([x[q1].max()])
        return new_df[new_names]

    grouped = get_maxima(dff)
    grouped2 = to_multiindex(grouped)
    grouped2 = grouped2.stack([1])[['Erms', 'ErmsNormal', 'ErmsFirst']]
    # remove one index level (only one value in this index: 0)
    grouped2.index = grouped2.index.droplevel(0)
    table = grouped2.rename(columns=renaming_dict).style.set_caption(
        'Conservative induced incident E_rms values for testing according to Tier 1').set_precision(3).set_properties(
            width='150px').set_table_attributes('border=1 cellspacing="0" cellpadding="10" style="text-align: center"')
    latex_caption = '[Same as AnnexP Table P5] Conservative induced incident E_rms values for testing according to Tier 1. Frequency: {} MHz, Birdcage: {}'.format(
        frequency, birdcage)
    save_table(table,
               'single_birdcage/{freq}/table_aggregated_{bc}_{freq}.png'.format(bc=birdcage, freq=frequency),
               show=True,
               latex_order=1,
               latex_caption=latex_caption)
    grouped2.rename(columns=renaming_dict).to_excel(r'D:\mrixvip\annexP\tableP5_{}.xlsx'.format(frequency))

grouped2.rename(columns=renaming_dict)

grouped2.rename(columns=renaming_dict).to_excel(r'D:\mrixvip\annexP\tableP1.xlsx')

# # B1 fields

for model, frequency in [(_m, _f) for _m in models for _f in [64, 128]]:
    birdcage = 'HP_B70_L60'
    dff = df[(df.model == model) & (df.freq == frequency) & (df.bc == birdcage) & (df.pos <= 900) & (df.pol == 'CP')]
    cols = [
        'pos',
        'B1SliceMeanRMS',
        'B1rms',
        'B1rms_empty',
        'ErmsHead_raw',
        'ErmsBody_raw',
        'ErmsLimbs_raw',
        'hSAR_raw',
        'wbSAR_raw',
        'pbSAR_raw',
    ]
    old_names = [
        'B1SliceMeanRMS', 'B1rms', 'B1rms_empty', 'ErmsHead_raw', 'ErmsBody_raw', 'ErmsLimbs_raw', 'hSAR_raw',
        'wbSAR_raw', 'pbSAR_raw'
    ]
    new_names = [
        'B1 RMS|Slice Mean', 'B1 RMS|Isocenter', 'B1 RMS|Empty Birdcage', 'Erms (not rescaled)|Head',
        'Erms (not rescaled)|Body', 'Erms (not rescaled)|Limbs', 'SAR (not rescaled)|Head',
        'SAR (not rescaled)|WholeBody', 'SAR (not rescaled)|PartialBody'
    ]
    dff = dff[cols].rename(columns={o: n for o, n in zip(old_names, new_names)})
    dff = to_multiindex(dff)
    table = dff.rename(columns=renaming_dict).style.background_gradient(
        cmap=cm).apply(highlight_max).set_table_attributes(
            'border=1 cellspacing="3" cellpadding="10" style="text-align: center"').set_precision(3).set_caption(
                '{} {}MHz'.format(model, frequency)).hide_index()  #.format("{0:.2g}")
    latex_caption = 'Raw data (not rescaled) from simulations. Frequency: {} MHz, Birdcage: {}'.format(
        frequency, birdcage)
    save_table(table,
               'single_birdcage/{freq}/table_NotScaled_{bc}_{m}_{freq}.png'.format(bc=birdcage, m=model,
                                                                                   freq=frequency),
               show=True,
               latex_order=3,
               latex_caption=latex_caption)

# # Get some more statistics between different models and birdcages


def create_agg(old_names, new_names):
    def agg(x):
        names = {}
        columns = []
        for q1, q2 in zip(old_names, new_names):
            names.update({
                '{}|max'.format(q2): x[q1].max(),
                '{}|mean'.format(q2): x[q1].mean(),
                '{}|std'.format(q2): x[q1].std(),
            })
            columns.extend(['{}|max'.format(q2), '{}|mean'.format(q2), '{}|std'.format(q2)])
        return pd.Series(names, index=columns)

    return agg


my_agg = create_agg(old_names=[
    'ErmsHead_1mu', 'ErmsBody_1mu', 'ErmsLimbs_1mu', 'ErmsHeadNormalOM', 'ErmsBodyNormalOM', 'ErmsLimbsNormalOM',
    'ErmsHeadFirstOM', 'ErmsBodyFirstOM', 'ErmsLimbsFirstOM'
],
                    new_names=[
                        'Erms|Head', 'Erms|Body', 'Erms|Limbs', 'ErmsNormal|Head', 'ErmsNormal|Body',
                        'ErmsNormal|Limbs', 'ErmsFirst|Head', 'ErmsFirst|Body', 'ErmsFirst|Limbs'
                    ])

for frequency in [64, 128]:
    grouped = df[df['freq'] == frequency].groupby(['freq', 'model']).apply(my_agg)
    grouped2 = to_multiindex(grouped)
    #
    table = grouped2.stack([0, 1, 2]).unstack([2, 3, 4])[[
        'Erms', 'ErmsNormal', 'ErmsFirst'
    ]].rename(columns=renaming_dict).style.background_gradient(cmap=cm).apply(highlight_max).set_precision(
        3).set_table_attributes('border=1 cellspacing="1" cellpadding="6"').set_caption(
            'Induced incident E_rms values at {} MHz accross all birdcages'.format(frequency))

    latex_caption = 'Max, mean and standard deviations are computed across all birdcages and all landmark positions'
    save_table(table,
               'extra_data/{freq}/per_model_std_allbc_{freq}.png'.format(freq=frequency),
               show=True,
               latex_order=5,
               latex_caption=latex_caption)

for frequency in [64, 128]:
    grouped = df[df['freq'] == frequency].groupby(['freq', 'model', 'bc']).apply(my_agg)
    grouped2 = to_multiindex(grouped)
    #
    table = grouped2.stack([0, 1, 2]).unstack([-3, -2, -1])[[
        'Erms', 'ErmsNormal', 'ErmsFirst'
    ]].rename(columns=renaming_dict).style.background_gradient(cmap=cm).apply(highlight_max).set_precision(
        3).set_table_attributes('border=1 cellspacing="1" cellpadding="6"').set_caption(
            'Induced incident E_rms values at {} MHz for each birdcages'.format(frequency))
    latex_caption = 'Max, mean and standard deviation are computed across all landmark positions.'
    save_table(table,
               'extra_data/{freq}/per_model-bc_{freq}.png'.format(freq=frequency),
               show=True,
               latex_order=7,
               latex_caption=latex_caption)

for frequency in [64, 128]:
    grouped = df[df['freq'] == frequency].groupby(['freq', 'model', 'bc']).apply(my_agg)
    cols = [
        'Erms|Head|max', 'Erms|Body|max', 'Erms|Limbs|max', 'ErmsNormal|Head|max', 'ErmsNormal|Body|max',
        'ErmsNormal|Limbs|max', 'ErmsFirst|Head|max', 'ErmsFirst|Body|max', 'ErmsFirst|Limbs|max'
    ]

    def _my_agg(x):
        old_names = cols
        new_names = [
            'Erms|Head', 'Erms|Body', 'Erms|Limbs', 'ErmsNormal|Head', 'ErmsNormal|Body', 'ErmsNormal|Limbs',
            'ErmsFirst|Head', 'ErmsFirst|Body', 'ErmsFirst|Limbs'
        ]
        names = {}
        columns = []
        for q1, q2 in zip(old_names, new_names):
            names.update({
                '{}|max'.format(q2): x[q1].max(),
                '{}|mean'.format(q2): x[q1].mean(),
                '{}|std'.format(q2): x[q1].std(),
            })
            columns.extend(['{}|max'.format(q2), '{}|mean'.format(q2), '{}|std'.format(q2)])
        return pd.Series(names, index=columns)

    grouped2 = grouped[cols].groupby(['freq', 'model']).apply(_my_agg)
    grouped2 = to_multiindex(grouped2)
    table = grouped2.rename(columns=renaming_dict).stack().unstack().style.background_gradient(
        cmap=cm).apply(highlight_max).set_caption(
            'E_{rms} values at %s MHz (mean/std of worst position across birdcages)' %
            frequency).set_precision(3).set_properties(
                width='20px').set_table_attributes('border=1 cellspacing="0" cellpadding="6"')
    latex_caption = 'First the max values for each birdcage are computed across all landmark positions.     This table reports the max, mean and standard deviation of these maxima across all birdcages.'
    save_table(table,
               'extra_data/{freq}/std_of_max_{freq}.png'.format(freq=frequency),
               show=True,
               latex_order=6,
               latex_caption=latex_caption)

for frequency in [64, 128]:

    def my_agg(x):
        old_names = [
            'ErmsHead_1mu', 'ErmsBody_1mu', 'ErmsLimbs_1mu', 'ErmsHeadNormalOM', 'ErmsBodyNormalOM',
            'ErmsLimbsNormalOM', 'ErmsHeadFirstOM', 'ErmsBodyFirstOM', 'ErmsLimbsFirstOM'
        ]
        new_names = [
            'Erms|Head', 'Erms|Body', 'Erms|Limbs', 'ErmsNormal|Head', 'ErmsNormal|Body', 'ErmsNormal|Limbs',
            'ErmsFirst|Head', 'ErmsFirst|Body', 'ErmsFirst|Limbs'
        ]
        names = {}
        columns = []
        for q1, q2 in zip(old_names, new_names):
            names.update({
                '{}'.format(q2): x[q1].max(),
            })
            columns.extend(['{}'.format(q2)])
        return pd.Series(names, index=columns)

    grouped = df[df['freq'] == frequency].groupby(['freq', 'model']).apply(my_agg)
    grouped2 = to_multiindex(grouped)
    table = grouped2.rename(columns=renaming_dict).stack([0, 1]).unstack(
        [2, 3]).style.background_gradient(cmap=cm).apply(highlight_max).set_caption(
            'Induced incident $E_{rms}$ values at %s MHz' % frequency).set_precision(3).set_properties(
                width='20px').set_table_attributes('border=1 cellspacing="0" cellpadding="6"')

    latex_caption = 'Worst cases for each model, across all positions and all birdcages, at {} MHz'.format(frequency)
    save_table(table,
               'extra_data/{freq}/per_model_allbc_{freq}.png'.format(freq=frequency),
               show=True,
               latex_order=8,
               latex_caption=latex_caption)

for frequency in [64, 128]:
    dff = df[(df.freq == frequency) & (df.pol == 'CP')]

    def get_maxima(x):
        old_names = [
            'ErmsHead_1mu', 'ErmsBody_1mu', 'ErmsLimbs_1mu', 'ErmsHeadNormalOM', 'ErmsBodyNormalOM',
            'ErmsLimbsNormalOM', 'ErmsHeadFirstOM', 'ErmsBodyFirstOM', 'ErmsLimbsFirstOM'
        ]
        new_names = [
            'Erms|Head', 'Erms|Body', 'Erms|Limbs', 'ErmsNormal|Head', 'ErmsNormal|Body', 'ErmsNormal|Limbs',
            'ErmsFirst|Head', 'ErmsFirst|Body', 'ErmsFirst|Limbs'
        ]
        new_df = pd.DataFrame()
        for q1, q2 in zip(old_names, new_names):
            new_df[q2] = np.array([x[q1].max()])
        return new_df[new_names]

    grouped = get_maxima(dff)
    grouped2 = to_multiindex(grouped)
    grouped2 = grouped2.stack([1])[['Erms', 'ErmsNormal', 'ErmsFirst']]
    # remove one index level (only one value in this index: 0)
    grouped2.index = grouped2.index.droplevel(0)
    table = grouped2.rename(columns=renaming_dict).style.set_caption(
        'Conservative induced incident E_rms values for testing according to Tier 1').set_precision(3).set_properties(
            width='150px').set_table_attributes('border=1 cellspacing="0" cellpadding="10" style="text-align: center"')

    latex_caption = 'Worst cases across all models, all birdcages, all positions at {} MHz'.format(frequency)
    save_table(table,
               'extra_data/{freq}/table_aggregated_allbc_{freq}.png'.format(freq=frequency),
               show=True,
               latex_order=10,
               latex_caption=latex_caption)

# # plots

#plt.style.use('ggplot')
plt.style.use('seaborn-whitegrid')

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.serif'] = 'Ubuntu'
plt.rcParams['font.monospace'] = 'Ubuntu Mono'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['axes.labelweight'] = 'bold'
plt.rcParams['axes.titlesize'] = 10
plt.rcParams['xtick.labelsize'] = 8
plt.rcParams['ytick.labelsize'] = 8
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 12
plt.rcParams['figure.figsize'] = (8, 6)

markers = {
    'Duke': 'o',
    'Fats': 's',
    'Ella': 'v',
    'Louis': 'd',
}

values_to_plot = [
    ('ErmsHead_1mu', 'E_rms [Head] 1muT [V/m]'),
    ('ErmsBody_1mu', 'E_rms [Trunk] 1muT [V/m]'),
    ('ErmsLimbs_1mu', 'E_rms [Limbs] 1muT [V/m]'),
    ('ErmsHeadNormalOM', 'E_rms [Head] Normal Operating Mode [V/m]'),
    ('ErmsBodyNormalOM', 'E_rms [Trunk] Normal Operating Mode [V/m]'),
    ('ErmsLimbsNormalOM', 'E_rms [Limbs] Normal Operating Mode [V/m]'),
    ('ErmsHeadFirstOM', 'E_rms [Head] First-Level Operating Mode [V/m]'),
    ('ErmsBodyFirstOM', 'E_rms [Trunk] First-Level Operating Mode [V/m]'),
    ('ErmsLimbsFirstOM', 'E_rms [Limbs] First-Level Operating Mode [V/m]'),
    ('ScalingNormal', 'B1 Scaling Factor Normal Operating Mode'),
    ('ScalingFirst', 'B1 Scaling Factor First-Level Operating Mode'),
]

for frequency in [64, 128]:
    for value, value_name in values_to_plot:
        grouped = df[df['freq'] == frequency].groupby(['model', 'pos']).agg({
            value: ['min', 'mean', 'max']
        }).unstack([0])
        ax = grouped.loc[:, (value, 'mean')].plot(marker='.', linewidth=0.5)  #plt.show()
        palette = sns.color_palette()
        models = list(grouped.columns.levels[2])  # all models
        models = [m for m in models if any(grouped.columns.get_level_values(2) == m)]  # drop models with no data
        for index, model in enumerate(models):
            ax.fill_between(grouped.index,
                            grouped.loc[:, (value, 'mean', model)],
                            grouped.loc[:, (value, 'max', model)],
                            alpha=.1,
                            color=palette[index])
            ax.fill_between(grouped.index,
                            grouped.loc[:, (value, 'min', model)],
                            grouped.loc[:, (value, 'mean', model)],
                            alpha=.1,
                            color=palette[index])
            ax.plot(grouped.loc[:, (value, 'max', model)], marker='.', linewidth=1.0, color=palette[index])
            ax.plot(grouped.loc[:, (value, 'min', model)], marker='.', linewidth=0.1, color=palette[index])

        ax.set_ylabel(value_name)
        ax.set_xlabel('landmark position [mm]')
        fig = plt.gcf()
        #plt.show()
        latex_caption = 'Mean, max and min values of {} across all birdcages at {} MHz'.format(value, frequency)
        save_figure(fig,
                    figname='extra_data/{freq}/{v}_{freq}.png'.format(v=value, freq=frequency),
                    dpi=250,
                    latex_order=20,
                    latex_caption=latex_caption)

# # Generate Latex file with all figures

figure_tplt = r"""
\begin{{figure}}
\centering
%
\includegraphics[width=.9\textwidth]{{{figpath}}}
%
\caption{{ {caption} }}
\end{{figure}}
"""

preamble = r"""
\documentclass[twoside,a4paper]{article}

\usepackage{graphicx}
\usepackage{grffile}
\usepackage{fancyhdr}
\usepackage{lscape}
\usepackage{array}
\usepackage{amsmath}
\usepackage{pdfpages}
\usepackage{float}
\usepackage{placeins}

\usepackage[T1]{fontenc}
\usepackage{a4wide}
\usepackage{amsfonts}
\usepackage{mathtools}
\usepackage{pdfpages}
\extrafloats{200}
"""

doc_tplt = r"""
{preamble}
\begin{{document}}
{content}
\end{{document}}
"""


def _escape(s):
    return s.replace('_', '\_')


content = []
for fig in sorted(_ALL_FIGURES, key=lambda x: x['order']):
    content.append(
        figure_tplt.format(figpath=os.path.relpath(fig['path'], OUTPUTS_DIR).replace('\\', '/'),
                           caption=_escape(fig['caption'])))
with open(os.path.join(OUTPUTS_DIR, 'figures.tex'), 'w') as f:
    f.write(doc_tplt.format(content=''.join(content), preamble=preamble))

# # Render as PDF file
import subprocess
latex_filepath = os.path.join(OUTPUTS_DIR, 'figures.tex')
cmd = ['pdflatex', '-interaction', 'nonstopmode', os.path.basename(latex_filepath)]
output = subprocess.check_output(cmd, cwd=os.path.dirname(latex_filepath),
                                 stderr=subprocess.STDOUT)  #, timeout=100)  # only with Python3
print('Created {}'.format(latex_filepath[0:-3] + 'pdf'))
