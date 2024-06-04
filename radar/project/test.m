clear; clc; close all
bandWidth = 250e6; %带宽
fc = 24e9; % 载波频率
T_chrip = 420e-6; %  chirp 持续时间
T_idle = 580e-6; % 两个chirp之间的间隔时间
c = physconst('LightSpeed'); %光速
lambda = c/fc;
%%

tau = [3e-9;3e-9+lambda/4*2/c];
t = linspace(0,T_chrip,200);
phi = fc .* tau + (bandWidth/2/T_chrip)*(2*tau*t-tau.^2);

figure;
subplot(311)
plot(phi(1,:))
subplot(312)
plot(phi(2,:))
subplot(313)
plot(phi(1,:)-phi(2,:))
ylim([-pi,pi]);