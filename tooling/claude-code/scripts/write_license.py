#!/usr/bin/env python3
"""Write SPDX license text to stdout. Usage: write_license.py LICENSE_ID YEAR AUTHOR"""
import sys

lid, year, author = sys.argv[1], sys.argv[2], sys.argv[3]

texts = {
    "Apache-2.0": f"""\
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions. "License" means the terms and conditions for use, reproduction,
      and distribution. "Licensor" means the copyright owner granting the License.
      "Legal Entity" means the union of the acting entity and all entities that
      control, are controlled by, or are under common control with that entity.
      "You" means an individual or Legal Entity exercising permissions granted by
      this License. "Source" form means the preferred form for making modifications.
      "Object" form means any form resulting from mechanical transformation of a
      Source form. "Work" means the work of authorship made available under the
      License. "Derivative Works" means any work based on the Work.
      "Contribution" means any work of authorship submitted to the Licensor.

   2. Grant of Copyright License. Each Contributor hereby grants to You a
      perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of, publicly
      display, publicly perform, sublicense, and distribute the Work and such
      Derivative Works in Source or Object form.

   3. Grant of Patent License. Each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable patent
      license to make, have made, use, offer to sell, sell, import, and otherwise
      transfer the Work.

   4. Redistribution. You may reproduce and distribute copies of the Work or
      Derivative Works in any medium, with or without modifications, provided that
      You meet the following conditions: (a) You must give recipients a copy of
      this License; (b) modified files must carry notices stating changes were
      made; (c) You must retain all copyright, patent, trademark, and attribution
      notices; (d) if the Work includes a NOTICE file, you must include a readable
      copy of the attribution notices within the Derivative Works.

   5. Submission of Contributions. Unless stated otherwise, Contributions shall be
      under the terms of this License.

   6. Trademarks. This License does not grant permission to use trade names,
      trademarks, or service marks of the Licensor.

   7. Disclaimer of Warranty. THE WORK IS PROVIDED "AS IS", WITHOUT WARRANTIES
      OR CONDITIONS OF ANY KIND, EXPRESS OR IMPLIED.

   8. Limitation of Liability. IN NO EVENT SHALL ANY CONTRIBUTOR BE LIABLE FOR
      ANY DAMAGES ARISING UNDER OR RELATED TO THIS LICENSE OR THE WORK.

   9. Accepting Warranty or Additional Liability is permitted when redistributing
      the Work, but only on Your own behalf, at Your sole risk and responsibility.

   END OF TERMS AND CONDITIONS

   Copyright {year} {author}

   Licensed under the Apache License, Version 2.0 (the "License"); you may not
   use this file except in compliance with the License. You may obtain a copy of
   the License at http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software distributed
   under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
   CONDITIONS OF ANY KIND, either express or implied. See the License for the
   specific language governing permissions and limitations under the License.
""",
    "BSD-3-Clause": f"""\
BSD 3-Clause License

Copyright (c) {year}, {author}
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
""",
    "Unlicense": """\
This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or distribute
this software, either in source code form or as compiled binaries, for any
purpose, commercial or non-commercial, and by any means.

In jurisdictions that recognize copyright laws, the author or authors of this
software dedicate any and all copyright interest in the software to the public
domain. We make this dedication for the benefit of the public at large and to
the detriment of our heirs and successors. We intend this dedication to be an
overt act of relinquishment in perpetuity of all present and future rights to
this software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <https://unlicense.org>
""",
}

if lid not in texts:
    sys.exit(f"Unknown license: {lid}. Supported: Apache-2.0, BSD-3-Clause, Unlicense")
print(texts[lid], end="")
