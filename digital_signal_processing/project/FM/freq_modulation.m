function [y] = freq_modulation(x, Fc, Fs, dim)
    len = size(x, dim);
    t_axis = (0:len - 1) / Fs;
    t_size = size(x);
    t_size(dim) = 1;
    t = repmat(reshape(t_axis, [ones(1, dim - 1), len, ones(1, ndims(x) - dim)]), t_size);

    int_x = cumsum(x, dim) / Fs;
    y = cos(2 * pi * Fc * t + 2 * pi * int_x);
end
