'use strict';

 

class MayanColor {
    static getHashScattered (hash) {
         
        let value = hash | 0;

        value = Math.imul(value ^ value >>> 16, 2246822507);
        value = Math.imul(value ^ value >>> 13, 3266489909);
        value = value ^ value >>> 16;

         
        return value >>> 0;
    }

    static getTextHash (text) {
         
        let hash = 0;

        for (let index = 0; index < text.length; index++) {
            const characterCode = text.charCodeAt(index);

            hash = (hash << 5) - hash + characterCode;

             
            hash = hash | 0;
        }

        return MayanColor.getHashScattered(hash);
    }

    static getChannelHexadecimal (value) {
        const valueScaled = Math.round(value * 255);
        const result = valueScaled.toString(16);

        if (result.length < 2) {
            return '0' + result;
        } else {
            return result;
        }
    }

    static getHexadecimalFromHSL (hue, saturation, lightness) {
         
        const lightnessUnit = lightness / 100;
        const saturationUnit = saturation / 100;

        const chroma = (
            1 - Math.abs(2 * lightnessUnit - 1)
        ) * saturationUnit;
        const huePrime = hue / 60;
        const chromaSecondary = chroma * (
            1 - Math.abs(huePrime % 2 - 1)
        );
        const offset = lightnessUnit - chroma / 2;

        let blue = 0;
        let green = 0;
        let red = 0;

        if (huePrime < 1) {
            red = chroma;
            green = chromaSecondary;
        } else if (huePrime < 2) {
            red = chromaSecondary;
            green = chroma;
        } else if (huePrime < 3) {
            green = chroma;
            blue = chromaSecondary;
        } else if (huePrime < 4) {
            green = chromaSecondary;
            blue = chroma;
        } else if (huePrime < 5) {
            red = chromaSecondary;
            blue = chroma;
        } else {
            red = chroma;
            blue = chromaSecondary;
        }

        const channelList = [red, green, blue];

        let result = '#';

        for (let index = 0; index < channelList.length; index++) {
            const channel = channelList[index] + offset;

            result = result + MayanColor.getChannelHexadecimal(channel);
        }

        return result;
    }

    static getColorFromText (text) {
         
        const textNormalized = text.trim().toLowerCase();

        if (textNormalized === '') {
            return null;
        }

        const hash = MayanColor.getTextHash(textNormalized);

        const hue = hash % MayanColor.autoHueCount;

        const saturationHash = Math.floor(hash / MayanColor.autoHueCount);
        const saturation = MayanColor.autoSaturationBase + (
            saturationHash % MayanColor.autoSaturationRange
        );

        const lightnessHash = Math.floor(
            saturationHash / MayanColor.autoSaturationRange
        );
        const lightness = MayanColor.autoLightnessBase + (
            lightnessHash % MayanColor.autoLightnessRange
        );

        return MayanColor.getHexadecimalFromHSL(hue, saturation, lightness);
    }

    static getColorRandom () {
        const value = Math.floor(
            Math.random() * MayanColor.randomValueCount
        );
        const result = value.toString(16);

        return '#' + result.padStart(6, '0');
    }
}

 
MayanColor.autoHueCount = 360;
MayanColor.autoLightnessBase = 35;
MayanColor.autoLightnessRange = 20;
MayanColor.autoSaturationBase = 55;
MayanColor.autoSaturationRange = 20;

MayanColor.randomValueCount = 16777216;
