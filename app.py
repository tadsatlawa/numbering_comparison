import functools
from functools import partial

import streamlit as st
import pandas as pd
import anarci
import hashlib

st.set_page_config(layout="wide")


def parse_int(pos: str) -> int:
    try:
        return int(pos)
    except:
        return int(pos[:-1])


colors = {
    'fw1': 'beige',
    'cdr1': 'lightgreen',
    'fw2': 'coral',
    'cdr2': 'darkgreen',
    'fw3': 'orange',
    'cdr3': 'forestgreen',
    'fw4': 'darkorange',
}


def color_wrapper(func):
    @functools.wraps(func)
    def wrapper_decorator(*args, **kwargs):
        ret = func(*args, **kwargs)
        return f'background-color: {colors[ret]}'

    return wrapper_decorator


@color_wrapper
def kabat_region(pos: str, chain: str):
    # http://people.cryst.bbk.ac.uk/~ubcg07s/misc/KabCDRDef.html
    posi = parse_int(pos)
    if chain == 'L':
        if posi < 24:
            return 'fw1'
        if posi <= 34:
            return 'cdr1'
        if posi < 50:
            return 'fw2'
        if posi <= 56:
            return 'cdr2'
        if posi < 89:
            return 'fw3'
        if posi <= 97:
            return 'cdr3'
        return 'fw4'
    elif chain == 'H':
        if posi < 31:
            return 'fw1'
        if posi <= 35:
            return 'cdr1'
        if posi < 50:
            return 'fw2'
        if posi <= 65:
            return 'cdr2'
        if posi < 95:
            return 'fw3'
        if posi <= 102:
            return 'cdr3'
        return 'fw4'


@color_wrapper
def imgt_region(pos: str, **kwargs):
    # http://people.cryst.bbk.ac.uk/~ubcg07s/misc/KabCDRDef.html
    posi = parse_int(pos)
    if posi < 27:
        return 'fw1'
    if posi <= 38:
        return 'cdr1'
    if posi < 56:
        return 'fw2'
    if posi <= 65:
        return 'cdr2'
    if posi < 105:
        return 'fw3'
    if posi <= 117:
        return 'cdr3'
    return 'fw4'


@color_wrapper
def chothia_region(pos: str, chain: str):
    posi = parse_int(pos)
    if chain == 'L':
        if posi < 26:
            return 'fw1'
        if posi <= 32:
            return 'cdr1'
        if posi < 50:
            return 'fw2'
        if posi <= 52:
            return 'cdr2'
        if posi < 91:
            return 'fw3'
        if posi <= 96:
            return 'cdr3'
        return 'fw4'
    elif chain == 'H':
        if posi < 26:
            return 'fw1'
        if posi <= 32:
            return 'cdr1'
        if posi < 52:
            return 'fw2'
        if posi <= 56:
            return 'cdr2'
        if posi < 96:
            return 'fw3'
        if posi <= 101:
            return 'cdr3'
        return 'fw4'


regions = {
    'IMGT': imgt_region,
    'Kabat': kabat_region,
}


def validate_df(df):
    aa_cols = [c for c in df.columns if c.startswith('aa_')]
    df_aa = df[aa_cols]

    assert df_aa.eq(df_aa.iloc[:, 0], axis=0).all(1).all(0)


st.title('Antibody numbering comparison')

seq = st.text_input('Input sequence')

selected_numberings = st.multiselect(
    'Which numberings?',
    ['IMGT', 'Aho', 'Kabat', 'Chothia', 'Martin'],
    ['IMGT', 'Kabat'])

st.markdown('''
Sample sequences to try:
* light: `DIQMTQTASSLSASLGDRVTISCRASQYINNNNNYLNWYQQKPDGTVTLLIYYTSILHSGVPSRFIGSGSGTDYSLTISNLDQEDIATYFCQQGYTLPLTFGAGTKLELK`
* heavy: `EVQLVESGGGLVQPGGSLRLSCAASGFTFSSYNMNWVRQAPGKGLEWVSYISSSSSTIYYADSVKGRFTISRDNAKNSLSLQMNSLRDEDTAVYYCARAYYYGMDVWGQGTTVTVSS`
* heavy (many insertions): `DVQLVESGGGLVQPGGSLRLSCVGSGFGPKVYCMGWFRQAPGKEREGVAAVDSEGNTSYVESVKGRFTISQDKDKNTVYLEMNNLKPEDTAMYYCAAELQIPLNRQVAGRSWHCPLLAPVSAGGRHSGVWGQGTQVTVS`
''')

if not seq:
    st.error('Sequence needed!')
    st.stop()

res = []
for num in selected_numberings:
    numbering, chain_type = anarci.number(seq, scheme=num.lower())
    st.write(numbering)
    numbering = [((str(n[0][0]) + n[0][1]).strip(), n[1]) for n in numbering if n[1] != '-']

    df = pd.DataFrame(numbering, columns=[num, f'aa_{num}'])  # .set_index(num)
    res.append(df)
df_all = pd.concat(res, axis=1)
validate_df(df_all)

aa_col = [c for c in df_all.columns if c.startswith('aa_')]
df_all.insert(0, 'aa', df_all[aa_col[0]])
# df_all.drop(columns=aa_col, inplace=True)
all_aa_same = df_all[aa_col].all()
st.dataframe(df_all)
df_all = df_all.transpose()

df_styled = df_all.style

for num in selected_numberings:
    if num in regions:
        fun = partial(regions[num], chain=chain_type)
        df_styled = df_styled.applymap(fun, subset=pd.IndexSlice[num, :])
# df_styled = df_all.style.background_gradient(imgt_region, subset=pd.IndexSlice['IMGT', :])

st.dataframe(df_styled)

if st.button('Export to xlsx'):
    hash = hashlib.md5(seq.encode('utf-8')).hexdigest()
    df_styled.to_excel(f'{hash}.xlsx')
    st.info(f'Saved to {hash}.xlsx')
