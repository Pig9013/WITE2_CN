"""Fill missing glyphs from locally installed fonts, without changing text."""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter,Options
from fontTools.merge import Merger
import tempfile
import shutil
import os

root=Path(__file__).resolve().parent
fonts_dir=Path(os.environ.get('WINDIR',r'C:\Windows'))/'Fonts'
out=root/'payload'/'overlay'/'Dat'/'Fonts'/'WitE2CN.ttf'
chars=(root/'payload'/'font-characters.txt').read_text(encoding='utf8')
font=TTFont(out);missing={ord(c) for c in chars if ord(c)>=32 and ord(c) not in font.getBestCmap() and c!='\ufeff'};font.close()
temp=Path(tempfile.mkdtemp(prefix='WitE2CN-font-'))
try:
    inputs=[str(out)]
    for name in ['arial.ttf','ebrima.ttf','LeelaUIb.ttf','malgun.ttf']:
        font=TTFont(fonts_dir/name)
        include=missing&set(font.getBestCmap())
        if not include:font.close();continue
        options=Options();options.layout_features=[];options.hinting=False;options.drop_tables+=['DSIG','GSUB','GPOS']
        subset=Subsetter(options=options);subset.populate(unicodes=include);subset.subset(font)
        for tag in list(font.keys()):
            if tag not in ['GlyphOrder','head','hhea','maxp','OS/2','hmtx','cmap','loca','glyf','name','post']:
                del font[tag]
        path=temp/name;font.save(path);font.close();inputs.append(str(path));missing-=include
    if missing:raise RuntimeError('Missing glyphs '+str(missing))
    if len(inputs)>1:
        # Drop shaping tables in merge inputs; game uses individual glyph atlases.
        base=TTFont(out)
        for glyph in base['glyf'].glyphs.values():
            glyph.removeHinting()
        for table in list(base.keys()):
            if table not in ['GlyphOrder','head','hhea','maxp','OS/2','hmtx','cmap','loca','glyf','name','post']:
                del base[table]
        base.save(temp/'base.ttf');inputs[0]=str(temp/'base.ttf')
        merged=Merger().merge(inputs)
        for record in merged['name'].names:
            if record.nameID in (1,3,4,6,16):
                record.string='WitE2CN'.encode(record.getEncoding())
        merged.save(out)
    print('Completed glyph coverage:',len(TTFont(out).getBestCmap()))
finally:
    assert temp.parent==Path(tempfile.gettempdir()) and temp.name.startswith('WitE2CN-font-')
    shutil.rmtree(temp)
