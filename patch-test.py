from diff_match_patch import diff_match_patch

a = "helwo\nmy name is sasha\ntesting123"
b = "hello\nmy name is sasha\ni like cake\ntesting123"

dmp = diff_match_patch()
p = dmp.patch_make(a, b)
unp = dmp.patch_make(b, a)
print(dmp.patch_toText(p))
print(dmp.patch_toText(unp))
