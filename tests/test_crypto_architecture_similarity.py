import unittest

from src.pipeline.crypto_architecture_similarity import build, jaccard


class Tests(unittest.TestCase):
    def test_jaccard(self):
        self.assertEqual(jaccard((1,0,1),(1,1,0)),1/3)

    def test_complete_matrix_and_pair_count(self):
        features=[f"v{i}" for i in range(10)]
        rows=[]
        for i in range(23):
            row={"asset_id":f"a{i}","symbol":f"A{i}","architecture_context":"x" if i<12 else "y","classification_status":"complete_human_verified"}
            row.update({f:str(int((i+int(f[1:]))%3==0)) for f in features}); rows.append(row)
        spec={"features":features,"inference":{"seed":1,"draws":100},"interpretation":"test"}
        result,pairs=build(rows,spec)
        self.assertEqual(result["pairs"],253)
        self.assertEqual(len(pairs),253)
        self.assertGreaterEqual(result["permutation_p_two_sided"],0)


if __name__=="__main__": unittest.main()
