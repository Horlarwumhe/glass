class HTTPCookie:
    def __init__(self):
        self._cookies = {}

    def add_cookie(self, name, value, **kw):
        cookie = Cookie(name, value, **kw)
        self._cookies[name] = cookie

    def __setitem__(self, key, value):
        self.add_cookie(key, value)

    def __getitem__(self, key):
        cookie = self._cookies.get(key)
        return cookie

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def as_http(self):
        out = []
        for _, cookie in self._cookies.items():
            out.append(cookie.as_http())
        return "\n".join(out)

    def as_wsgi(self):
        out = []
        for _, cookie in self._cookies.items():
            out.append(cookie.as_wsgi())
        return out

    def __repr__(self):
        out = [self.__class__.__name__]
        for name, cookie in self._cookies.items():
            out.append("%s=%s" % (name, cookie.value))
        return ", ".join(out)

    def __iter__(self):
        for _, cookie in self._cookies.items():
            yield cookie


class Cookie:
    default = "path domain lax same_site, samesite"

    def __init__(self, name, value, **kwargs):
        self.name = name
        self.value = value
        self._attrs = kwargs

    def __str__(self):
        out = []
        out.append("%s=%s" % (self.name, self.value))
        for attr in self._attrs:
            out.append(" %s=%s" % (attr, self._attrs.get(attr, "")))
        return ";".join(out)

    def __getitem__(self, key):
        return self._attrs.get(key, None)

    def __setitem__(self, key, value):
        self._attrs[key] = value

    def as_http(self):
        return "Set-cookie: ", str(self)

    def as_wsgi(self):
        # session=eyJuYW0; HttpOnly; Path=/
        out = ["%s=%s" % (self.name, self.value)]
        for key, value in self._attrs.items():
            if key.lower() == 'httponly':
                key = 'HttpOnly'
            elif key.lower() == 'samesite':
                key = 'SameSite'
            else:
                # secure,max-age,
                key = key.replace('_', '-').title()
            if isinstance(value, bool):
                # httonly=True, change to
                # HttpOnly;
                if value:
                    out.append(key)
                else:
                    continue
            else:

                out.append("%s=%s" % (key, value))
        return ("Set-Cookie", '; '.join(out))

    def __repr__(self):
        out = ["Cookie: %s=%s" % (self.name, self.value)]

        for name, value in self._attrs.items():
            if not value:
                out.append("%s" % (self.name))
            else:
                out.append("%s=%s" % (name, value))
        return ", ".join(out)
