# -*- coding: utf-8 -*-

"""Construct classifier-ready dataset for a member of parliament (MP).

This submodule constructs a datamatrix and a target array for an MP using
the function 'dataset_X_y', which calls each of the functions prefixed with
'feat_' and concatenates their returned feature vectors into a datapoint for
each iteration over a list of votes cast by an MP.
"""

from os.path import abspath, dirname
import os

PARENTDIR = dirname(dirname(abspath(__file__)))
os.sys.path.insert(0, PARENTDIR)

from dataretrieval.odagetter import OdaGetter
from dataretrieval.odaparsers import single_mp, mp_votes, vote_case
from resume_lda import lda_topics
import xml.etree.ElementTree as ET
import numpy as np


GETTER = OdaGetter()


def feat_party(caseid):
    """Return feature array representing the party of the proposing MP (PMP).

    Parameters
    ----------
    caseid : id-integer
        Int-type corresponding to the case-id with which the cases voted on in
        the parliament, in the current term, are indexed on www.oda.ft.dk.

    Returns
    -------
    out : feature-array
        A numpy array of n_parties length conataining 0's and a 1 at the
        appropriate entry corresponding to how the parties are indexed on
        www.oda.ft.dk.

        Example
        -------
        array([ 0.,  0.,  0.,  0.,  1.,  0.,  0.,  0.])
    """

    parties = ['Venstre', 'Socialdemokratiet', 'Socialistisk Folkeparti',
               'Dansk Folkeparti', 'Radikale Venstre', 'Enhedslisten',
               'Liberal Alliance', 'Det Konservative Folkeparti']

    try:
        aktoerid = GETTER.get_sagaktoer(caseid, 19)  # 19 is the typeid for
        # the "proposing politician
    except IndexError:
        print "No actor with role id 19 was found for\ caseid %d. Returning "\
            "0-array." % caseid
        return np.zeros(len(parties))

    data = single_mp(aktoerid)

    try:
        root = ET.fromstring(data['biografi'].encode('utf-16'))
    except:
        print "No info ('biografi') was found for MP: %s. Returning "\
            "0-array." % aktoerid
        return np.zeros(len(parties))

    party = root.find('party').text

    feat_array = np.zeros(len(parties))

    for i, p in enumerate(parties):
        if party == p:
            feat_array[i] = 1
            break
    else:
        print "No party was found for caseid: %d. Returning 0-array." % caseid

    return feat_array


def feat_category(case_categoryid):
    """Return feature array representing the category of the proposition.

    Parameters
    ----------
    case_categoryid : id-integer
        Int-type corresponding to the particular category of the case in
        question, pertaining to the way the categorys are indexed on
        www.oda.ft.dk.

    Returns
    -------
    out : feature-array
        A numpy array of n_categories length, conataining 0's and a 1 at the
        appropriate entry corresponding to how the parties are indexed on
        www.oda.ft.dk.
    """

    feat_array = np.zeros(17)  # There are 17 different categories
    feat_array[case_categoryid-1] = 1

    return feat_array


def feat_L_or_B(case_nummerprefix):
    """Return feature array for type of proposition: bill 'L' or motion 'B'.

    Parameters
    ----------
    case_nummerprefix : prefix-string
        Str-type corresponding to the case being a bill ('L') or a motion ('B')

    Returns
    -------
    out : feature-array
        A numpy array of length 2, conataining a 0 and a 1.
        [1, 0] for 'L' and [0, 1] for 'B'.
    """

    if case_nummerprefix == 'L':
        return np.array([1., 0.])
    elif case_nummerprefix == 'B':
        return np.array([0., 1.])
    else:
        return np.array([0., 0.])


def remove_zero_cols(X):
    """Remove columns in a datamatrix that only contains zeros.

    Note that this function is not used in 'dataset_X_y' since the internal
    structure of features is lost when zero-columns are removed. It is,
    however, included in this submodule because it can be useful in cases
    where the datamatrices should be treated as black box system.

    Parameters
    ----------
    X : array-type
        Numpy array or matrix type of n_rows, n_cols > 1.

    Returns
    -------
    out : array-type with no zero-cols
        The given X numpy array or matrix with zero-coloumns removed.
    """

    zero_cols = []
    for i in range(X.shape[1]):
        if sum(X[:, i]) == 0:
            zero_cols.append(i)

    X = np.delete(X, zero_cols, 1)
    return X


def dataset_X_y(aktoerid, force=False):
    """Return classifier-ready dataset for an MP.

    Return a clean dataset X of features for every case the given MP has
    voted in, along with a target vector y, representing his/her vote in said
    case.

    Parameters
    ----------
    aktoerid : id-integer
        Int-type corresponding to the actor-id with which the MP is 
        indexed by on www.oda.ft.dk.

    Returns
    -------
    out1 : feature-array
        A data matrix of numpy.array type, each row containing the features of
        a particular case in which the MP in question voted.

        Example
        ------- 
        array([[ 0.        ,  1.        ,  0.        , ...,  0.59463238,
                 0.        ,  0.        ],
               ...,
               [ 0.        ,  1.        ,  0.        , ...,  0.06455698,
                 0.        ,  0.04262148]])

    out2 : target-array
        A numpy.array of classindices, representing the binary vote result.

        Example
        -------
        array([2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
               1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 1, 2, 1, 1,
               1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 1,
               1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 2, 2,
               2, 2, 2, 2, 2, 1, 1, 1, 2, 2, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1])
    """

    if force is False:    
        try:
            X = np.load(PARENTDIR + '/storing/matrices/X_%d.npy' % aktoerid)
            y = np.load(PARENTDIR + '/storing/matrices/y_%d.npy' % aktoerid)
            return X, y 
        except IOError:
                pass

    
    # Get list of votes that the given MP has cast
    mp_votes_list = mp_votes(aktoerid)

    # Get full list of votes in parliament. This is needed since we are only
    # interested in votes that are of typeid = 1, i.e. final votes, and this
    # information is not available in mp_votes_list. Note that the key 'typeid'
    # is also present in mp_votes_list, but that it here represents the MP's
    # decision in that vote, and carries no information about what type of
    # vote it was.
    all_votes_list = GETTER.get_afstemning()

    # The database has a lot of dublicates, so to avoid these we add processed
    # cases to an array that has to be checked for every iteration.
    processed_cases = []

    X, y = [], []
    for mp_vote in mp_votes_list:

        # Check if vote is final, i.e. typeid = 1
        continue_after_check = True
        for vote in all_votes_list:
            if mp_vote['afstemningid'] == vote['id']:
                if vote['typeid'] != 1:
                    continue_after_check = False
                    print "Vote not final"
                    break

        if continue_after_check is False:
            continue

        # Instantiate case profile to extract features from
        case = vote_case(mp_vote['afstemningid'])

        if case['id'] in processed_cases:
            print "Dublicate found! Vote %d in case %d" % (
                mp_vote['afstemningid'], case['id'])
            continue
        else:
            processed_cases.append(case['id'])

        print "\nProcessing vote %d in case %d - MP id %d\n" % (
            mp_vote['afstemningid'], case['id'], aktoerid)

        X_case = []

        X_case.extend(feat_party(case['id']))
        print "Successfully added party\t to features for\
        caseid\t %d" % case['id']

        X_case.extend(feat_category(case['kategoriid']))
        print "Successfully added category\t to features for\
        caseid\t %d" % case['id']

        X_case.extend(feat_L_or_B(case['nummerprefix']))
        print "Successfully added numberprefix\t to features for\
        caseid\t %d" % case['id']

        X_case.extend(lda_topics(case['resume']))
        print "Successfully added LDA topics\t to features for\
        caseid\t %d" % case['id']

        X.append(X_case)
        y.append(mp_vote['typeid'])

    return np.array(X), np.array(y)
