"""
This directory is setup with configurations to run the main functional test.

Inspired in bcbio-nextgen code
"""
from __future__ import print_function
import os
import unittest

from nose.plugins.attrib import attr


def annotate(fn, read_file, load=False, create=True):
    import argparse
    args = argparse.Namespace()
    args.hairpin = "data/examples/annotate/hairpin.fa"
    args.sps = "hsa"
    args.gtf = "data/examples/annotate/hsa.gff3"
    args.add_extra = True
    args.out_format = "gtf"
    from mirtop.mirna import fasta, mapper
    precursors = fasta.read_precursor(args.hairpin, args.sps)
    matures = mapper.read_gtf_to_precursor(args.gtf)
    args.precursors = precursors
    args.matures = matures
    args.database = mapper.guess_database(args.gtf)
    from mirtop.mirna import annotate
    from mirtop.gff import body
    if not load:
        reads = read_file(fn, args)
    else:
        reads = read_file
    if create:
        ann = annotate.annotate(reads, matures, precursors)
        body = body.create(ann, "miRBase21", "Example", args)
    return body


class FunctionsTest(unittest.TestCase):
    """Setup a full automated analysis and run the pipeline.
    """
    @attr(database=True)
    def test_database(self):
        from mirtop.mirna import mapper
        db = mapper.guess_database("data/examples/annotate/hsa.gff3")
        print("Database is %s" % db)
        if db != "miRBasev21":
            raise ValueError("%s not eq to miRBasev21" % db)

    @attr(read=True)
    def test_read(self):
        from mirtop.mirna import mapper, fasta
        from mirtop.libs import logger
        logger.initialize_logger("test_read_files", True, True)
        map_mir = mapper.read_gtf_to_precursor(
            "data/examples/annotate/hsa.gff3")
        print(map_mir)
        if map_mir["hsa-let-7a-1"]["hsa-let-7a-5p"][0] != 5:
            raise ValueError("GFF is not loaded correctly.")
        fasta_precursor = fasta.read_precursor(
            "data/examples/annotate/hairpin.fa", "hsa")
        print(fasta_precursor)
        fasta_precursor2 = fasta.read_precursor(
            "data/examples/annotate/hairpin.fa", None)
        print(fasta_precursor2)
        if fasta_precursor != fasta_precursor2:
            raise ValueError("species value generates two different dicts.")
        # read data/aligments/let7-perfect.bam
        return True

    @attr(read_genomic=True)
    def test_read_genomic(self):
        from mirtop.mirna import mapper
        from mirtop.libs import logger
        logger.initialize_logger("test_read_files", True, True)
        map_mir = mapper.read_gtf_to_mirna("data/examples/annotate/hsa.gff3")
        print(map_mir)
        # if map_mir["hsa-let-7a-1"]["hsa-let-7a-5p"][0] != 5:
        #    raise ValueError("GFF is not loaded correctly.")
        return True

    @attr(read_line=True)
    def test_read_line(self):
        """Read GFF/GTF line"""
        from mirtop.gff.body import read_gff_line
        with open("data/examples/gff/2samples.gff") as inh:
            for line in inh:
                print(read_gff_line(line))

    @attr(code=True)
    def test_code(self):
        """testing code correction function"""
        from mirtop.mirna.realign import make_id, read_id

        def _convert(s, test, reverse=False):
            code = read_id(s) if reverse else make_id(s)
            if code != test:
                raise ValueError("%s didn't result on %s but in %s" %
                                 (s, test, code))

        _convert("AAACCCTTTGGG", "@#%$")
        _convert("AAACCCTTTGGGA", "@#%$@2")
        _convert("AAACCCTTTGGGAT", "@#%$g1")
        _convert("@#%$", "AAACCCTTTGGG", True)
        _convert("@#%$@2", "AAACCCTTTGGGA", True)
        _convert("@#%$g1", "AAACCCTTTGGGAT", True)

        if make_id("AGTFCVS"):
            raise ValueError("This should be False. Not valid sequence.")
        if read_id("asD(-"):
            raise ValueError("This should be False, Not valid code.")

    @attr(cigar=True)
    def test_cigar(self):
        """testing cigar correction function"""
        cigar = [[0, 14], [1, 1], [0, 5]]
        from mirtop.mirna.realign import cigar_correction, make_cigar, \
            cigar2snp, expand_cigar
        fixed = cigar_correction(cigar, "AAAAGCTGGGTTGAGGAGGA",
                                 "AAAAGCTGGGTTGAGAGGA")
        if not fixed[0] == "AAAAGCTGGGTTGAGGAGGA":
            raise ValueError("Sequence 1 is not right.")
        if not fixed[1] == "AAAAGCTGGGTTGA-GAGGA":
            raise ValueError("Sequence 2 is not right.")
        if not make_cigar("AAA-AAATAAA", "AGACAAA-AAA") == "MAMD3MI3M":
            raise ValueError("Cigar not eq to MAMD3MI3M: %s" %
                             make_cigar("AAA-AAATAAA", "AGACAAA-AAA"))
        # test expand cigar
        if not expand_cigar("3MA3M") == "MMMAMMM":
            raise ValueError("Cigar 3MA3M not eqaul to MMMAMMM but to %s" %
                             expand_cigar("3MA3M"))
        # test cigar to snp
        if not cigar2snp("3MA3M", "AAATCCC")[0] == [3, "A", "T"]:
            raise ValueError("3MA3M not equal AAATCCC but %s" %
                             cigar2snp("3MA3M", "AAATCCC"))

    @attr(sequence=True)
    def test_is_sequence(self):
        """testing if string is valid sequence"""
        from mirtop.mirna.realign import is_sequence
        if not is_sequence("ACTGC"):
            raise ValueError("ACTGC should return true.")
        if is_sequence("AC2TGC"):
            raise ValueError("AC2TGC should return false.")

    @attr(locala=True)
    def test_locala(self):
        """testing pairwise alignment"""
        from mirtop.mirna.realign import align
        print("\nExamples of perfect match, deletion, mutation")
        print(align("TGAGTAGTAGGTTGTATAGTT", "TGAGGTAGTAGGTTGTATAGTT")[0])
        print(align("TGAGGTGTAGGTTGTATAGTT", "TGAGGTAGTAGGTTGTATAGTT")[0])
        print(align("TGAGGTAGTAGGCTGTATAGTT", "TGAGGTAGTAGGTTGTATAGTT")[0])
        print(align("TGANTAGTAGNTTGTATNGTT", "TGAGTAGTAGGTTGTATAGTTT")[0])
        print(align("TGANTAGTNGNTTGTATNGTT", "TGAGTATAGGCCTTGTATAGTT")[0])
        print(align("NCANAGTCCAAGNTCATN", "TCATAGTCCAAGGTCATG")[0])

    @attr(reverse=True)
    def test_reverse(self):
        """Test reverse complement function"""
        from mirtop.mirna.realign import reverse_complement
        print("Testing ATGC complement")
        if "GCAT" != reverse_complement("ATGC"):
            raise ValueError("ATGC complement is not: %s" %
                             reverse_complement("ATGC"))

    @attr(class_gff=True)
    def test_class(self):
        """Test class to read GFF line"""
        from mirtop.gff.classgff import feature
        gff = feature("hsa-let-7a-5p\tmiRBasev21\tisomiR\t4\t25\t0\t+\t.\t"
                      "Read hsa-let-7a-1_hsa-let-7a-5p_5:26_-1:-1_mut:"
                      "null_add:null_x861; UID bhJJ5WJL2;"
                      " Name hsa-let-7a-5p; Parent hsa-let-7a-1;"
                      " Variant iso_5p:+1,iso_3p:-1; Cigar 22M;"
                      " Expression 861; Filter Pass; Hits 1;")
        print(gff.columns)
        print(gff.attributes)

    @attr(merge=True)
    def test_merge(self):
        """Test merge functions"""
        from mirtop.gff import merge
        example_line = "hsa-let-7a-5p\tmiRBasev21\tisomiR\t4\t25"
        if merge._chrom(example_line) != "hsa-let-7a-5p":
            raise ValueError("Chrom should be hsa-let-7a-5p.")
        if merge._start(example_line) != "4":
            raise ValueError("Start should be 4.")
        expression = merge._convert_to_string({'s': 1, 'x': 2}, ['s', 'x'])
        print(merge._fix("hsa-let-7a-5p\tmiRBasev21\tisomiR\t4\t25\t0\t+\t.\t"
                         "Read hsa-let-7a-1_hsa-let-7a-5p_5:26_-1:-1_mut:"
                         "null_add:null_x861; UID bhJJ5WJL2;"
                         " Name hsa-let-7a-5p; Parent hsa-let-7a-1;"
                         " Variant iso_5p:+1,iso_3p:-1; Cigar 22M;"
                         " Expression 861; Filter Pass; Hits 1;", expression))
        if expression != "1,2":
            raise ValueError("This is wrong: %s" % expression)

    @attr(mature=True)
    def test_variant(self):
        """testing get mature sequence"""
        from mirtop.mirna import fasta, mapper
        from mirtop.mirna.realign import get_mature_sequence, \
            align_from_variants
        precursors = fasta.read_precursor("data/examples/annotate/hairpin.fa",
                                          "hsa")
        matures = mapper.read_gtf_to_precursor(
            "data/examples/annotate/hsa.gff3")
        res = get_mature_sequence("GAAAATTTTTTTTTTTAAAAG", [5, 15])
        if res != "AAAATTTTTTTTTTTAAAA":
            raise ValueError("Results for GAAAATTTTTTTTTTTAAAAG was %s" % res)
        mature = get_mature_sequence(precursors["hsa-let-7a-1"],
                                     matures["hsa-let-7a-1"]["hsa-let-7a-5p"])
        if mature != "GGGATGAGGTAGTAGGTTGTATAGTTTTAG":
            raise ValueError("Results for hsa-let-7a-5p is %s" % mature)

        res = align_from_variants("AGGTAGTAGGTTGTATAGTT", mature,
                                  "iso_5p:-2")
        if res:
            raise ValueError("Wrong alignment for test 1 %s" % res)
        res = align_from_variants("GATGAGGTAGTAGGTTGTATAGTT", mature,
                                  "iso_5p:+2")
        if res:
            raise ValueError("Wrong alignment for test 2 %s" % res)
        res = align_from_variants("AGGTAGTAGGTTGTATAGTTTT", mature,
                                  "iso_5p:-2,iso_add:2")
        if res:
            raise ValueError("Wrong alignment for test 3 %s" % res)
        res = align_from_variants("AGGTAGTAGGTTGTATAGTTTT", mature,
                                  "iso_5p:-2,iso_3p:2")
        if res:
            raise ValueError("Wrong alignment for test 4 %s" % res)
        res = align_from_variants("AGGTAGTAGGTTGTATAG", mature,
                                  "iso_5p:-2,iso_3p:-2")
        if res:
            raise ValueError("Wrong alignment for test 5 %s" % res)
        res = align_from_variants("AGGTAGTAGGTTGTATAGAA", mature,
                                  "iso_5p:-2,iso_3p:-2,iso_add:2")
        if res:
            raise ValueError("Wrong alignment for test 6 %s" % res)
        res = align_from_variants("AGGTAGTAGGATGTATAGTT", mature,
                                  "iso_5p:-2,iso_snp_central")
        if not res:
            if res[0][0] != 10:
                raise ValueError("Wrong alignment for test 7 %s" % res)
        res = align_from_variants("AGGTAGTAGGATGTATAGAA", mature,
                                  "iso_5p:-2,iso_3p:-2,iso_add:2")
        if res:
            raise ValueError("Wrong alignment for test 8 %s" % res)

    @attr(alignment=True)
    def test_alignment(self):
        """testing alignments function"""
        from mirtop.bam import bam
        print("\nlast1D\n")
        print(annotate("data/aligments/let7-last1D.sam", bam.read_bam))
        # mirna TGAGGTAGTAGGTTGTATAGTT
        # seq   AGAGGTAGTAGGTTGTA
        print("\n1D\n")
        print(annotate("data/aligments/let7-1D.sam", bam.read_bam))
        # mirna TGAGGTAG-TAGGTTGTATAGTT
        # seq   TGAGGTAGGTAGGTTGTATAGTTA
        print("\nlast7M1I\n")
        print(annotate("data/aligments/let7-last7M1I.sam", bam.read_bam))
        # mirna TGAGGTAGTAGGTTGTATAGTT
        # seq   TGAGGTAGTAGGTTGTA-AGT
        print("\nmiddle1D\n")
        print(annotate("data/aligments/let7-middle1D.sam", bam.read_bam))
        # mirna TGAGGTAGTAGGTTGTATAGTT
        # seq   TGAGGTAGTAGGTTGTATAGTT
        print("\nperfect\n")
        print(annotate("data/aligments/let7-perfect.sam", bam.read_bam))
        # mirna TGAGGTAGTAGGTTGTATAGTT
        # seq   TGAGGTAGTAGGTTGTATAG (3tt 3TT)
        print("\ntriming\n")
        print(annotate("data/aligments/let7-triming.sam", bam.read_bam))

    @attr(seqbuster=True)
    def test_seqbuster(self):
        """testing reading seqbuster files function"""
        from mirtop.libs import logger
        logger.initialize_logger("test", True, True)
        logger = logger.getLogger(__name__)
        from mirtop.importer import seqbuster
        print("\nperfect\n")
        annotate("data/examples/seqbuster/reads20.mirna", seqbuster.read_file)
        print("\naddition\n")
        annotate("data/examples/seqbuster/readsAdd.mirna", seqbuster.read_file)

    @attr(srnabench=True)
    def test_srnabench(self):
        """testing reading seqbuster files function"""
        from mirtop.libs import logger
        logger.initialize_logger("test", True, True)
        logger = logger.getLogger(__name__)
        from mirtop.importer import srnabench
        annotate("data/examples/srnabench", srnabench.read_file, create=False)

    @attr(prost=True)
    def test_prost(self):
        """testing reading prost files function"""
        from mirtop.libs import logger
        logger.initialize_logger("test", True, True)
        logger = logger.getLogger(__name__)
        from mirtop.mirna import fasta
        precursors = fasta.read_precursor("data/examples/annotate/hairpin.fa",
                                          "hsa")
        fn = "data/examples/prost/prost.example.txt"
        from mirtop.importer import prost
        reads = prost.read_file(
            fn, precursors, "miRBasev21", "data/examples/annotate/hsa.gff3")
        annotate("data/example/prost/prost.example.txt", reads, True)

    @attr(gff=True)
    def test_gff(self):
        """testing GFF function"""
        from mirtop.libs import logger
        logger.initialize_logger("test", True, True)
        logger = logger.getLogger(__name__)
        from mirtop.bam import bam
        bam_fn = "data/aligments/let7-perfect.sam"
        annotate(bam_fn, bam.read_bam)
        return True

    @attr(collapse=True)
    def test_collapse(self):
        """testing GFF function"""
        from mirtop.libs import logger
        logger.initialize_logger("test", True, True)
        logger = logger.getLogger(__name__)
        from mirtop.bam import bam
        bam_fn = "data/aligments/collapsing-isomirs.sam"
        annotate(bam_fn, bam.read_bam)
        return True

    @attr(counts=True)
    def test_counts(self):
        """testing convert_gff_counts in convert.py function"""
        from mirtop.libs import logger
        from mirtop.gff.convert import convert_gff_counts
        import argparse

        logger.initialize_logger("test counts", True, True)
        logger = logger.getLogger(__name__)

        args = argparse.Namespace()
        args.hairpin = "data/examples/annotate/hairpin.fa"
        args.sps = "hsa"
        args.gtf = "data/examples/annotate/hsa.gff3"
        args.gff = 'data/examples/synthetic/let7a-5p.gtf'
        args.out = 'data/examples/synthetic'
        args.add_extra = True
        convert_gff_counts(args)
        os.remove(os.path.join(args.out, "expression_counts.tsv"))

        return True

    @attr(stats=True)
    def test_stats(self):
        """testing stats function"""
        from mirtop.gff import stats
        from mirtop import version
        df = stats._calc_stats("data/examples/gff/correct_file.gff")
        stats._dump_log(df, version, None)
        print(df)

    @attr(variant=True)
    def test_variant(self):
        """testing parsing string variant"""
        from mirtop.gff import body
        gff = body.read_variant("iso_5p:-1,iso_add:2,iso_snp_central_supp")
        if len(gff) != 3:
            raise ValueError("Error size of output. Expectd 3.")
        if cmp(["iso_5p", "iso_add", "iso_snp_central_supp"], gff.keys()):
            raise ValueError("Not found expected keys.")
        if not isinstance(gff["iso_snp_central_supp"], bool):
            raise ValueError("iso_snp_central_supp should be boolean.")
        if cmp([-1, 2, True], gff.values()):
            raise ValueError("Not found expected Values.")

    @attr(validator=True)
    def test_validator(self):
        """test validator functions"""
        from mirtop.gff.validator import _check_file
        _check_file("data/examples/gff/2samples.gff")
        _check_file("data/examples/gff/coldata_missing.gff")
        _check_file("data/examples/gff/3wrong_type.gff")
