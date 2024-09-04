clc; clear; close all;

% 参数设置
fs = 1e3; % 采样频率
fc = 100; % 载波频率
t = 0:1 / fs:1 - 1 / fs; % 时间向量

%% 生成锯齿波基带信号
baseband_signal = 50 * sawtooth(2 * pi * 5 * t);

%% 使用 fmmod 进行 FM 调制
% modulated_signal = fmmod(baseband_signal, fc, fs, 1);
modulated_signal = freq_modulation(baseband_signal, fc, fs, 2);

% 添加高斯白噪声
noisy_signal = awgn(modulated_signal, 100, 'measured');

%% 使用 fmdemod 进行 FM 解调
demodulated_signal = fmdemod(noisy_signal, fc, fs, 1);

%% 绘图
n = length(t);
f = (0:n - 1) * (fs / n); % 频率向量

baseband_spectrum = abs(fft(baseband_signal));
modulated_spectrum = abs(fft(modulated_signal));
demodulated_spectrum = abs(fft(demodulated_signal));

% 绘制基带信号、中频信号、解调信号和它们的幅度谱
figure;

subplot(2, 2, 1);
plot(t, baseband_signal);
title('基带信号');
xlabel('时间 (秒)');
ylabel('幅度');

subplot(2, 2, 2);
plot(t, demodulated_signal);
title('解调信号');
xlabel('时间 (秒)');
ylabel('幅度');

subplot(2, 2, 3);
plot(t, noisy_signal);
title('调制信号');
xlabel('时间 (秒)');
ylabel('幅度');

subplot(2, 2, 4);
plot(f, modulated_spectrum);
title('调制信号的幅度谱');
xlabel('频率 (Hz)');
ylabel('幅度');

% 调整幅度谱的显示范围
xlim([0 fs / 2]);
