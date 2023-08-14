import logging

from ..kore._jinyaml import FileLocation
from ..kore._core import DeepChain
from ..kore._komp import Komponent
from ._kube import KubeApp, Resource
from . import templates

logger = logging.getLogger(__name__)


class KustApp(KubeApp):
    #def kreate_files(self):
    #    super().kreate_files()
    #    # kreate the Kustomization again, but now the App has added all
    #    # resources
    #    #kust = self.kreate_komponent("Kustomization")
    #    #kust.kreate_file()

    def register_std_templates(self) -> None:
        super().register_std_templates()
        self.register_template_class(Kustomization, package=templates)
        self.register_template_class(AntiAffinityPatch, package=templates)
        self.register_template_class(HttpProbesPatch, package=templates)

    def kreate_komponents_from_strukture(self):
        super().kreate_komponents_from_strukture()
        for res in self.komponents:
            if isinstance(res, Resource):
                self.kreate_patches(res)

    def kreate_patch(
            self,
            res: Resource,
            kind: str,
            shortname: str = None,
            **kwargs):
        cls = self.kind_classes[kind]
        templ = self.kind_templates[kind]
        if issubclass(cls, Patch):
            return cls(res, kind, shortname, template=templ, **kwargs)
        raise TypeError(
            f"class for {kind}.{shortname} is not a Patch but {cls}")

    def kreate_patches(self, res: Resource) -> None:
        if "patches" in res.strukture:
            for kind in res.strukture.patches:
                for shortname in res.strukture.patches[kind]:
                    self.kreate_patch(res, kind=kind, shortname=shortname)


class Kustomization(Komponent):
    def resources(self):
        return [
            res for res in self.app.komponents if isinstance(
                res, Resource)]

    def patches(self):
        return [res for res in self.app.komponents if isinstance(res, Patch)]

    @property
    def filename(self):
        return "kustomization.yaml"


class Patch(Komponent):
    def __init__(
            self,
            target: Resource,
            kind: str = None,
            shortname: str = None,
            template: FileLocation = None,
            **kwargs):
        self.target = target
        Komponent.__init__(
            self,
            target.app,
            kind=kind,
            shortname=shortname,
            template=template,
            **kwargs)

    def __str__(self):
        return (f"<Patch {self.target.kind}.{self.target.shortname}"
                f":{self.kind}.{self.shortname}>")

    def _template_vars(self):
        return {**super()._template_vars(), "target": self.target}

    def _find_strukture(self):
        root_strukture = super()._find_strukture()
        typename = self.kind
        targt_konf = self.target.strukture.get("patches", {})
        if typename in targt_konf and self.shortname in targt_konf[typename]:
            logger.debug(
                f"using embedded strukture {typename}.{self.shortname}"
                f" from {self.target.kind}.{self.target.shortname}")
            # The embedded_strukture is first, since the root_strukture will contain
            # all default values
            embedded_strukture = targt_konf[typename][self.shortname]
            return DeepChain(embedded_strukture, root_strukture)
        return root_strukture


class HttpProbesPatch(Patch):
    pass


class AntiAffinityPatch(Patch):
    pass
