import numpy as np
from obspy.io.sac import SACTrace
from os.path import join, basename
import sys
import re
from matplotlib.ticker import MultipleLocator
import matplotlib.pyplot as plt
from os.path import join, abspath, dirname
from seispy.geo import cosd, sind
from seispy.decov import decovit
from scipy.interpolate import griddata


def joint_stack(energy_r, energy_cc, energy_tc, weight=[0.4, 0.3, 0.3]):
    energy_r = energy_r / np.max(energy_r)
    energy_cc = energy_cc / np.max(energy_cc)
    energy_tc = energy_tc / np.max(energy_tc)
    return np.exp(np.log(energy_r) * weight[0] + np.log(energy_cc) * weight[1] - np.log(energy_tc) * weight[2])


class RFAni():
    def __init__(self, sacdatar, tb, te, val=10):
        self.tb = tb
        self.te = te
        self.sacdatar = sacdatar
        self.baz_stack(val=val)
        # self.para = readpara(para=join(path, 'raysum-params'))
        # self.baz, self.datar, self.datat = readrf(path, self.para, join(path, 'sample.geom'))
        self.init_ani_para()
        self.fvd, self.deltat = np.meshgrid(self.fvd_1d, self.deltat_1d)
        self.nb = int((self.tb + self.sacdatar.shift) / self.sacdatar.sampling)
        self.ne = int((self.te + self.sacdatar.shift) / self.sacdatar.sampling)

    def baz_stack(self, val=10):
        self.stack_range = np.arange(0, 360, val)
        self.rft_baz = np.zeros([self.stack_range.shape[0], self.sacdatar.rflength])
        self.rfr_baz = np.zeros_like(self.rft_baz)
        self.count_baz = np.zeros(self.stack_range.shape[0])
        search_range = np.append(self.stack_range, self.stack_range[-1]+val)
        for i in range(self.stack_range.size):
            idx = np.where((self.sacdatar.bazi > search_range[i]) & (self.sacdatar.bazi < search_range[i+1]))[0]
            self.count_baz[i] = idx.size
            if idx.size != 0:
                self.rft_baz[i] = np.mean(self.sacdatar.datat[idx], axis=0)
                self.rfr_baz[i] = np.mean(self.sacdatar.datar[idx], axis=0)

    def init_ani_para(self):
        self.deltat_1d = np.arange(0, 1.55, 0.05)
        self.fvd_1d = np.arange(0, 365, 5)

    def cut_energy_waveform(self, idx, nb, ne):
        engr = np.zeros([nb.shape[0], nb.shape[1], self.ne-self.nb])
        for i in range(nb.shape[0]):
            for j in range(nb.shape[1]):
                engr[i, j, :] = self.rfr_baz[idx, nb[i, j]:ne[i, j]]
        return engr

    def radial_energy_max(self):
        energy = np.zeros([self.fvd.shape[0], self.fvd.shape[1], self.ne-self.nb])
        # tmp_data = np.zeros(self.ne-self.nb)
        for i, baz in enumerate(self.stack_range):
            t_corr = (self.deltat / 2) * cosd(2 * (self.fvd - baz))
            nt_corr = (t_corr / self.sacdatar.sampling).astype(int)
            new_nb = self.nb - nt_corr
            new_ne = self.ne - nt_corr
            energy += self.cut_energy_waveform(i, new_nb, new_ne)
        energy = np.max(energy ** 2, axis=2)
        energy /= np.max(np.sum(self.rfr_baz[:, self.nb:self.ne], axis=0)**2)
        return energy

    def xyz2grd(self, energy):
        self.fvd, self.deltat = np.meshgrid(self.fvd_1d, self.deltat_1d)
        return griddata(self.ani_points, energy, (self.fvd, self.deltat))

    def rotate_to_fast_slow(self):
        self.ani_points = np.empty([0, 2])
        for f in self.fvd_1d:
            for d in self.deltat_1d:
                self.ani_points = np.vstack((self.ani_points, np.array([f, d])))
        energy_cc = np.zeros(self.ani_points.shape[0])
        energy_tc = np.zeros(self.ani_points.shape[0])
        raw_energy_r = np.sum(np.sum(self.rfr_baz[:, self.nb:self.ne], axis=0) ** 2 - np.sum(self.rfr_baz[:, self.nb:self.ne] ** 2, axis=0))
        raw_energy_t = np.sum(np.sum(self.rft_baz[:, self.nb:self.ne] ** 2, axis=0))
        for i, point in enumerate(self.ani_points):
            nt_corr = (point[1]/2 / self.sacdatar.sampling).astype(int)
            nt_fast = np.arange(self.nb, self.ne) + nt_corr
            nt_slow = np.arange(self.nb, self.ne) - nt_corr
            fcr = np.zeros(self.ne-self.nb)
            fcr_sq = np.zeros(self.ne-self.nb)
            fct = 0
            for j, baz in enumerate(self.stack_range):
                data_fast = self.rfr_baz[j, nt_slow] * cosd(point[0] - baz) + self.rft_baz[j, nt_slow] * sind(point[0] - baz)
                data_slow = -self.rfr_baz[j, nt_fast] * sind(point[0] - baz) + self.rft_baz[j, nt_fast] * cosd(point[0] - baz)
                back_rotate_data_r = data_fast * cosd(point[0] - baz) - data_slow * sind(point[0] - baz)
                back_rotate_data_t = data_fast * sind(point[0] - baz) + data_slow * cosd(point[0] - baz)
                fcr += back_rotate_data_r
                fcr_sq += back_rotate_data_r ** 2
                # print(np.sum(back_rotate_data_t ** 2), np.sum(self.rft_baz[j, self.nb:self.ne] ** 2))
                fct += np.sum(back_rotate_data_t ** 2)
            energy_cc[i] = np.sum(fcr ** 2 - fcr_sq) / raw_energy_r
            energy_tc[i] = fct/ raw_energy_t
        # energy_cc /= np.max(np.abs(energy_cc))
        energy_tc /= np.max(np.abs(energy_tc))
        return self.xyz2grd(energy_cc), self.xyz2grd(energy_tc)

    def plot_correct(self, fvd=0, dt=0.44, enf=80, outpath=None):
        nt_corr = int((dt/2 / self.sacdatar.sampling))
        nt_fast = np.arange(self.nb, self.ne) + nt_corr
        nt_slow = np.arange(self.nb, self.ne) - nt_corr
        time_axis = np.arange(self.nb, self.ne) * self.sacdatar.sampling - self.sacdatar.shift
        bound = np.zeros_like(time_axis)
        ml = MultipleLocator(5)
        plt.figure(figsize=(8, 6))
        axr = plt.subplot(1, 2, 1)
        axt = plt.subplot(1, 2, 2)
        for j, baz in enumerate(self.sacdatar.baz):
            rot_fast = self.rfr_baz[j] * cosd(fvd - baz) + self.rft_baz[j] * sind(fvd - baz)
            rot_slow = -self.rfr_baz[j] * sind(fvd - baz) + self.rft_baz[j] * cosd(fvd - baz)
            data_fast = rot_fast[self.nb-nt_corr:self.ne-nt_corr]
            data_slow = rot_slow[self.nb+nt_corr:self.ne+nt_corr]
            back_rotate_data_r = data_fast * cosd(fvd - baz) - data_slow * sind(fvd - baz)
            back_rotate_data_t = data_fast * sind(fvd - baz) + data_slow * cosd(fvd - baz)
            amp = back_rotate_data_r * enf + baz
            axr.plot(time_axis, amp, linewidth=0.2, color='black')
            axr.fill_between(time_axis, amp, bound + baz, where=amp > baz, facecolor='red', alpha=0.5)
            axr.fill_between(time_axis, amp, bound + baz, where=amp < baz, facecolor='blue', alpha=0.5)
            amp = back_rotate_data_t * enf + baz
            axt.plot(time_axis, amp, linewidth=0.2, color='black')
            axt.fill_between(time_axis, amp, bound + baz, where=amp > baz, facecolor='red', alpha=0.5)
            axt.fill_between(time_axis, amp, bound + baz, where=amp < baz, facecolor='blue', alpha=0.5)
        for ax in [axr, axt]:
            ax.grid(color='gray', linestyle='--', linewidth=0.4, axis='x')
            ax.set_xlim(-1, 10)
            ax.set_xticks(np.arange(0, 11, 1))
            ax.set_ylim(0, 360)
            ax.set_yticks(np.arange(0, 360+30, 30))
            ax.yaxis.set_minor_locator(ml)
            ax.set_xlabel('Time after P(s)')
        axr.set_ylabel('Back-azimuth ($^\circ$)')
        axr.set_title('R component')
        axt.set_title('T component')
        if outpath is not None and isinstance(outpath, str):
            plt.savefig(join(outpath, 'rf_corrected.pdf'))

    def search_peak_list(self, energy, opt='max'):
        if opt == 'max':
            ind = np.argwhere(energy == np.max(energy))
        elif opt == 'min':
            ind = np.argwhere(energy == np.min(energy))
        else:
            raise ValueError('\'opt\' must be max or min')
        print(ind.shape)
        return self.ani_points[ind][:, 0], self.ani_points[ind][:, 1]

    def search_peak(self, energy, opt='max'):
        if opt == 'max':
            ind = np.argwhere(energy == np.max(energy))
        elif opt == 'min':
            ind = np.argwhere(energy == np.min(energy))
        else:
            raise ValueError('\'opt\' must be max or min')
        best_fvd = []
        best_dt = []
        for i, j in ind:
            best_fvd.append(self.fvd[i, j])
            best_dt.append(self.deltat[i, j])
        return np.array(best_fvd), np.array(best_dt)

    def joint_ani(self, weight=[0.5, 0.3, 0.2]):
        self.energy_r = self.radial_energy_max()
        self.energy_cc, self.energy_tc = self.rotate_to_fast_slow()
        self.energy_joint = joint_stack(self.energy_r, self.energy_cc, self.energy_tc, weight)
        self.bf, self.bt = self.search_peak(self.energy_joint, opt='max')
        return self.bf, self.bt

    def plot_polar(self, show=True, outpath='./'):
        fig, axes = plt.subplots(2, 2, figsize=(8, 7), subplot_kw={'projection': 'polar'}, constrained_layout=True)
        axs = [axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]]
        energy_all = [self.energy_r, self.energy_cc, self.energy_tc, self.energy_joint]
        energy_title = ['R cosine energy', 'R cross-correlation', 'T energy', 'Joint']
        for ax, energy, title in zip(axs, energy_all, energy_title):
            # ax.set_polar(True)
            ax.set_theta_direction(-1)
            ax.set_theta_zero_location("N")
            eng = ax.pcolor(np.radians(self.fvd), self.deltat, energy, cmap='jet', shading='auto')
            ax.grid(True, color='lightgray', linewidth=0.5)
            ax.scatter(np.radians(self.bf), self.bt, color='white', marker='X', s=48)
            ax.set_xticks(np.radians(np.arange(0, 360, 30)))
            ax.set_yticks(np.arange(0, 1.5, 0.5))
            ax.set_title(title)
            fig.colorbar(eng, ax=ax)
        if show:
            plt.show()
        fig.savefig(join(outpath, 'joint_ani_'+self.sacdatar.staname+'.png'), bbox_inches='tight')


if __name__ == "__main__":
    path = join(thispath, 'ani_0_4')
    rfani = RFAni(path, 3, 7)
    energy_r = rfani.radial_energy_max()
    energy_cc, energy_tc = rfani.rotate_to_fast_slow()
    energy_joint = rfani.joint(energy_r, energy_cc, energy_tc)
    bf, bt = rfani.search_peak(energy_joint, opt='max')
    # bft, btt = rfani.search_peak(energy_tc, opt='min')
    # print(bft, btt)
    rfani.plot_polar(energy_joint, bf, bt)
    # rfani1 = RFAni(path, -2, 30)
    # rfani1.plot_correct()
