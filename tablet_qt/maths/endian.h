/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

#pragma once

/*

Detecting endianness across compilers: do it at runtime.
- https://stackoverflow.com/questions/8978935/detecting-endianness

*/


// Possible endian types.
enum class Endian { BigEndian, LittleEndian };


// What endianness does this computer use for integers?
// See references in the code.
Endian endianByteOrder();

// What endianness does this computer use for floating point words?
// See references in the code.
Endian endianFloatWordOrder();
