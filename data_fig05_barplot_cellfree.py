########################################
#   data_fig05_barplot_cellfree.py
#
#   Description. Script used to generate data for Fig. 5 of the paper regarding
#   the cell-free curves. You should choose the estimator among the three avai-
#   lable.
#
#   Author. @victorcroisfelt
#
#   Date. December 27, 2021
#
#   This code is part of the code package used to generate the numeric results
#   of the paper:
#
#   Croisfelt, V., Abrão, T., and Marinello, J. C., “User-Centric Perspective in
#   Random Access Cell-Free Aided by Spatial Separability”, arXiv e-prints, 2021.
#
#   Available on:
#
#                   https://arxiv.org/abs/2107.10294
#
#   Comment. You need to run:
#
#       - plot_fig05_barplot.py
#
#   to actually plot the figure using the data generated by this script.
#   
#   Please, make sure that you have the files produced by:
#       
#       - lookup_fig05_06_delta.py
#       - lookup_fig05_06_best_pair.py
#
########################################
import numpy as np

import time

########################################
# Preamble
########################################
np.random.seed(42)

########################################
# System parameters
########################################

# Define number of APs
L = 64

# Define number of antennas per AP
N = 8

# UL transmit power
p = 100

# DL transmit power per AP
ql = 200/L

# Define noise power
sigma2 = 1

# Number of RA pilot signals
taup = 5

########################################
# SELECTION
########################################

# Choose the estimator
estimator = "est1"
estimator = "est2"
estimator = "est3"

########################################
# Lookup table
########################################

# Load best pair look up table
load = np.load("lookup/lookup_fig05_best_pair_" + estimator + ".npz", allow_pickle=True)
best_pair_lookup = load["best_pair"]
best_pair_lookup = best_pair_lookup.item()

# Load possible values of delta for Estimator 3
if estimator == "est3":

    load = np.load("lookup/lookup_fig05_06_delta.npz", allow_pickle=True)
    delta_lookup = load["delta"]
    delta_lookup = delta_lookup.item()

########################################
# Geometry
########################################

# Define square length
squareLength = 400

# Create square grid of APs
APperdim = int(np.sqrt(L))
APpositions = np.linspace(squareLength/APperdim, squareLength, APperdim) - squareLength/APperdim/2
APpositions = APpositions + 1j*APpositions[:, None]
APpositions = APpositions.reshape(L)

########################################
# Simulation parameters
########################################

# Set the number of setups
numsetups = 100

# Set the number of channel realizations
numchannel = 100

# Range of collision sizes
collisions = np.arange(1, 11)

########################################
# Simulation
########################################
print("--------------------------------------------------")
print("Data Fig 05: barplot -- cell-free")
print("\testimator: " + estimator)
print("\tN = " + str(N))
print("--------------------------------------------------\n")

# Store total time
total_time = time.time()

# Store enumeration of L
enumerationL = np.arange(L)

# Prepare to save NMSE stats
nmse = np.zeros((3, collisions.size))


#####


# Generate noise realizations at APs
n_ = np.sqrt(sigma2/2)*(np.random.randn(numsetups, N, L, numchannel) + 1j*np.random.randn(numsetups, N, L, numchannel))

# Generate noise realization at UEs
eta = np.sqrt(sigma2/2)*(np.random.randn(numsetups, collisions.max(), numchannel) + 1j*np.random.randn(numsetups, collisions.max(), numchannel))


# Go through all collision sizes
for cs, collisionSize in enumerate(collisions):

    # Storing time
    timer_start = time.time()

    # Print current data point
    print(f"\tcollision: {cs}/{collisions.size-1}")


    #####
    # Generating UEs
    #####

    # Generate UEs locations
    UElocations = squareLength*(np.random.rand(numsetups, collisionSize) + 1j*np.random.rand(numsetups, collisionSize))

    # Compute UEs distances to each AP
    UEdistances = np.abs(UElocations[:, :, np.newaxis] - APpositions)

    # Compute average channel gains according to Eq. (1)
    channel_gains = 10**((94.0 - 30.5 - 36.7 * np.log10(np.sqrt(UEdistances**2 + 10**2)))/10)

    # Generate normalized channel matrix for each AP equipped with N antennas
    Gnorm_ = np.sqrt(1/2)*(np.random.randn(numsetups, N, collisionSize, L, numchannel) + 1j*np.random.randn(numsetups, N, collisionSize, L, numchannel))

    # Compute channel matrix
    G_ = np.sqrt(channel_gains[:, None, :, :, None]) * Gnorm_

    # Compute received signal according to Eq. (4)
    Yt_ = np.sqrt(p * taup) * G_.sum(axis=2) +  n_

    # Store l2-norms of Yt
    Yt_norms = np.linalg.norm(Yt_, axis=1)

    # Obtain pilot activity vector according to Eq. (8)
    atilde_t = (1/N) * Yt_norms**2
    atilde_t[atilde_t < sigma2] = 0.0

    # Extract current Csize and Lmax 
    (Csize, Lmax) = best_pair_lookup[(collisionSize, N)]

    # Prepare to save inner NMSE
    nmse_in = np.zeros((numsetups, collisionSize, numchannel))


    # Go through all setups
    for ss in range(numsetups):

        # Go through all channel realizations
        for ch in range(numchannel):

            # Obtain set of pilot-serving APs (Definition 2)
            Pcal = np.argsort(atilde_t[ss, :, ch])[-Lmax:]
            Pcal = np.delete(Pcal, atilde_t[ss, Pcal, ch] == 0)


            #####
            # SUCRe - step 2
            #####


            if estimator == 'est3':

                # Denominator according to Eqs. (34) and (35)
                den = np.sqrt(N * (atilde_t[ss, :, ch] - sigma2).sum())

                # Compute precoded DL signal according to Eq. (35)
                Vt_ = np.sqrt(ql) * (Yt_[ss][:, Pcal, ch] / den)

            else:

                # Compute precoded DL signal according to Eq. (10)
                Vt_ = np.sqrt(ql) * (Yt_[ss][:, Pcal, ch] / Yt_norms[ss, Pcal, ch][None, :])

            # Compute true total UL signal power of colliding UEs 
            # according to Eq. (16)
            alpha_true = p * taup * channel_gains[ss, :, Pcal].sum()

            # Go through all colliding UEs
            for k in range(collisionSize):

                # Compute received DL signal at UE k according to Eq. 
                # (12)
                z_k = np.sqrt(taup) * (G_[ss][:, k, Pcal, ch].conj() * Vt_).sum() + eta[ss, k, ch]

                # Obtain set of nearby APs of UE k (Definition 1)
                Ccal_k = np.argsort(ql * channel_gains[ss, k, :])[-Csize:]

                # Obtain natural set of nearby APs of UE k (Definition 1)
                checkCcal_k = enumerationL[ql * channel_gains[ss, k, :] > sigma2]

                if len(checkCcal_k) == 0:
                    checkCcal_k = np.array([np.argmax(ql * channel_gains[ss, k, :])])

                if len(Ccal_k) > len(checkCcal_k):
                    Ccal_k = checkCcal_k


                #####
                # Estimation
                #####


                # Compute constants
                cte = z_k.real/np.sqrt(N)
                num = np.sqrt(ql * p) * taup * channel_gains[ss, k, Ccal_k]

                
                if estimator == 'est1':

                    # Compute estimate according to Eq. (28)
                    alphahat = ((num.sum()/cte)**2) - sigma2

                elif estimator == 'est2':

                    num23 = num**(2/3)
                    cte2 = (num23.sum()/cte)**2

                    # Compute estimate according to Eq. (32)
                    alphahat = (cte2 * num23 - sigma2).sum()

                elif estimator == 'est3':

                    # Define compensation factor in Eq. (39)
                    delta = delta_lookup[(collisionSize, N, Lmax)]

                    # Compute new constant according to Eq. (38)
                    underline_cte = delta * (z_k.real - sigma2)/np.sqrt(N)

                    # Compute estimate according to Eq. (40)
                    alphahat = (num.sum() / underline_cte)**2

                # Compute own total UL signal power in Eq. (15)
                gamma = p * taup * channel_gains[ss, k, Ccal_k].sum()

                # Avoiding underestimation
                if alphahat < gamma:
                    alphahat = gamma

                # Get and store inner loop stats
                nmse_in[ss, k, ch] = (np.abs(alphahat - alpha_true)**2)/(alpha_true**2)

    # Average out channel realizations
    nmse_in = nmse_in.mean(axis=-1)

    # Save NMSE stats
    nmse[:, cs] = np.stack((np.percentile(nmse_in, 25), np.median(nmse_in), np.percentile(nmse_in, 75)))
    
    print("\t[collision] elapsed " + str(np.round(time.time() - timer_start, 4)) + " seconds.\n")

print("total simulation time was " + str(np.round(time.time() - total_time, 4)) + " seconds.\n")
print("wait for data saving...\n")

# Save simulation results
np.savez('data/fig05_barplot_cellfree_' + estimator + '.npz',
    nmse=nmse
)

print("the data has been saved in the /data folder.\n")

print("------------------- all done :) ------------------")